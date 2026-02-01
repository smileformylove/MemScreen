### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

"""
Main Memory implementation.

This module contains the primary Memory class that provides memory storage,
retrieval, and management capabilities.
"""

import asyncio
import concurrent
import gc
import hashlib
import json
import logging
import os
import uuid
import warnings

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Optional, Union, Literal, List
from functools import lru_cache

from .base import MemoryBase
from .models import MemoryConfig, MemoryItem, MemoryType

# OPTIMIZATION: Use intelligent caching system
from ..cache import IntelligentCache, cached_search

# Global search cache instance
_search_cache = IntelligentCache(max_size=1000, default_ttl=300)  # 5 min TTL

# Import from sibling modules
from ..llm import LlmFactory
from ..embeddings import EmbedderFactory
from ..vector_store import VectorStoreFactory
from ..storage import SQLiteManager
from ..prompts import (
    PROCEDURAL_MEMORY_SYSTEM_PROMPT,
    get_update_memory_messages,
)
from ..utils import (
    get_fact_retrieval_messages,
    parse_messages,
    parse_vision_messages,
    process_telemetry_filters,
    remove_code_blocks,
    extract_python_dict,
    extract_json_from_response,
)
from ..telemetry import capture_event

logger = logging.getLogger(__name__)


def _build_filters_and_metadata(
    *,  # Enforce keyword-only arguments
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None,
    actor_id: Optional[str] = None,  # For query-time filtering
    input_metadata: Optional[Dict[str, Any]] = None,
    input_filters: Optional[Dict[str, Any]] = None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Constructs metadata for storage and filters for querying based on session and actor identifiers.

    This helper supports multiple session identifiers (`user_id`, `agent_id`, and/or `run_id`)
    for flexible session scoping and optionally narrows queries to a specific `actor_id`. It returns two dicts:

    1. `base_metadata_template`: Used as a template for metadata when storing new memories.
       It includes all provided session identifier(s) and any `input_metadata`.
    2. `effective_query_filters`: Used for querying existing memories. It includes all
       provided session identifier(s), any `input_filters`, and a resolved actor
       identifier for targeted filtering if specified by any actor-related inputs.

    Actor filtering precedence: explicit `actor_id` arg → `filters["actor_id"]`
    This resolved actor ID is used for querying but is not added to `base_metadata_template`,
    as the actor for storage is typically derived from message content at a later stage.

    Args:
        user_id (Optional[str]): User identifier, for session scoping.
        agent_id (Optional[str]): Agent identifier, for session scoping.
        run_id (Optional[str]): Run identifier, for session scoping.
        actor_id (Optional[str]): Explicit actor identifier, used as a potential source for
            actor-specific filtering. See actor resolution precedence in the main description.
        input_metadata (Optional[Dict[str, Any]]): Base dictionary to be augmented with
            session identifiers for the storage metadata template. Defaults to an empty dict.
        input_filters (Optional[Dict[str, Any]]): Base dictionary to be augmented with
            session and actor identifiers for query filters. Defaults to an empty dict.

    Returns:
        tuple[Dict[str, Any], Dict[str, Any]]: A tuple containing:
            - base_metadata_template (Dict[str, Any]): Metadata template for storing memories,
              scoped to the provided session(s).
            - effective_query_filters (Dict[str, Any]): Filters for querying memories,
              scoped to the provided session(s) and potentially a resolved actor.
    """

    base_metadata_template = deepcopy(input_metadata) if input_metadata else {}
    effective_query_filters = deepcopy(input_filters) if input_filters else {}

    # ---------- add all provided session ids ----------
    session_ids_provided = []

    if user_id:
        base_metadata_template["user_id"] = user_id
        effective_query_filters["user_id"] = user_id
        session_ids_provided.append("user_id")

    if agent_id:
        base_metadata_template["agent_id"] = agent_id
        effective_query_filters["agent_id"] = agent_id
        session_ids_provided.append("agent_id")

    if run_id:
        base_metadata_template["run_id"] = run_id
        effective_query_filters["run_id"] = run_id
        session_ids_provided.append("run_id")

    if not session_ids_provided:
        raise ValueError("At least one of 'user_id', 'agent_id', or 'run_id' must be provided.")

    # ---------- optional actor filter ----------
    resolved_actor_id = actor_id or effective_query_filters.get("actor_id")
    if resolved_actor_id:
        effective_query_filters["actor_id"] = resolved_actor_id

    return base_metadata_template, effective_query_filters


class Memory(MemoryBase):
    """
    Main Memory implementation for storing, retrieving, and managing memories.

    This class provides a comprehensive memory management system with support for:
    - Semantic memory (facts and knowledge)
    - Episodic memory (events and experiences)
    - Procedural memory (skills and procedures)
    - Vector-based similarity search
    - History tracking
    """

    def __init__(self, config: MemoryConfig = MemoryConfig()):
        """
        Initialize the Memory system.

        Args:
            config (MemoryConfig): Configuration for the memory system.
        """
        self.config = config

        self.custom_fact_extraction_prompt = self.config.custom_fact_extraction_prompt
        self.custom_update_memory_prompt = self.config.custom_update_memory_prompt
        self.embedding_model = EmbedderFactory.create(
            self.config.embedder.provider,
            self.config.embedder.config,
            self.config.vector_store.config,
        )
        self.vector_store = VectorStoreFactory.create(
            self.config.vector_store.provider, self.config.vector_store.config
        )
        self.llm = LlmFactory.create(self.config.llm.provider, self.config.llm.config)
        self.mllm = LlmFactory.create(self.config.mllm.provider, self.config.mllm.config)

        # OPTIMIZATION: Enable batch database writing by default
        enable_batch_writing = getattr(self.config, 'enable_batch_writing', True)
        self.db = SQLiteManager(self.config.history_db_path, enable_batch_writing=enable_batch_writing)

        self.collection_name = self.config.vector_store.config.collection_name
        self.api_version = self.config.version

        # OPTIMIZATION: Performance tuning flags
        self.optimization_enabled = getattr(self.config, 'optimization_enabled', True)
        self.skip_simple_fact_extraction = getattr(self.config, 'skip_simple_fact_extraction', True)
        self.enable_search_cache = getattr(self.config, 'enable_search_cache', True)
        self.batch_size = getattr(self.config, 'batch_size', 50)

        # Performance monitoring
        self._stats = {
            "add_calls": 0,
            "search_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Initialize graph store if enabled
        self.enable_graph = getattr(self.config, 'enable_graph', False)
        self.graph = None

        if self.enable_graph:
            try:
                from ..graph import GraphStoreFactory, EntityExtractor
                from ..graph.models import GraphConfig

                graph_config = getattr(self.config, 'graph_store', None)
                if graph_config is None:
                    graph_config = {"provider": "memory"}

                self.graph = GraphStoreFactory.create(
                    graph_config.get("provider", "memory"),
                    graph_config.get("config", {})
                )
                self.entity_extractor = EntityExtractor(self.llm)
                logger.info("Graph store initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize graph store: {e}")
                self.enable_graph = False
                self.graph = None

        # Set up telemetry vector store (separate from main vector store)
        home_dir = os.path.expanduser("~")
        memscreen_dir = os.environ.get("memscreen_DIR") or os.path.join(home_dir, ".memscreen")

        # Create a copy of the config for telemetry to avoid side effects
        telemetry_config = deepcopy(self.config.vector_store.config)
        telemetry_config.collection_name = "memscreenmigrations"

        if self.config.vector_store.provider in ["faiss", "qdrant"]:
            provider_path = f"migrations_{self.config.vector_store.provider}"
            telemetry_config.path = os.path.join(memscreen_dir, provider_path)
            os.makedirs(telemetry_config.path, exist_ok=True)

        self._telemetry_vector_store = VectorStoreFactory.create(
            self.config.vector_store.provider, telemetry_config
        )
        capture_event("memscreen.init", self, {"sync_type": "sync"})

    @classmethod
    def from_config(cls, config_dict: Dict[str, Any]):
        """
        Create a Memory instance from a configuration dictionary.

        Args:
            config_dict (Dict[str, Any]): Configuration dictionary.

        Returns:
            Memory: A new Memory instance.
        """
        try:
            config = cls._process_config(config_dict)
            config = MemoryConfig(**config_dict)
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            raise
        return cls(config)

    @staticmethod
    def _process_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process configuration dictionary.

        Args:
            config_dict (Dict[str, Any]): Raw configuration dictionary.

        Returns:
            Dict[str, Any]: Processed configuration dictionary.
        """
        if "graph_store" in config_dict:
            if "vector_store" not in config_dict and "embedder" in config_dict:
                config_dict["vector_store"] = {}
                config_dict["vector_store"]["config"] = {}
                config_dict["vector_store"]["config"]["embedding_model_dims"] = config_dict["embedder"]["config"][
                    "embedding_dims"
                ]
        try:
            return config_dict
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            raise

    def add(
        self,
        messages,
        *,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        infer: bool = True,
        memory_type: Optional[str] = None,
        prompt: Optional[str] = None,
    ):
        """
        Create a new memory.

        Adds new memories scoped to a single session id (e.g. `user_id`, `agent_id`, or `run_id`). One of those ids is required.

        Args:
            messages (str or List[Dict[str, str]]): The message content or list of messages
                (e.g., `[{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]`)
                to be processed and stored.
            user_id (str, optional): ID of the user creating the memory. Defaults to None.
            agent_id (str, optional): ID of the agent creating the memory. Defaults to None.
            run_id (str, optional): ID of the run creating the memory. Defaults to None.
            metadata (dict, optional): Metadata to store with the memory. Defaults to None.
            infer (bool, optional): If True (default), an LLM is used to extract key facts from
                'messages' and decide whether to add, update, or delete related memories.
                If False, 'messages' are added as raw memories directly.
            memory_type (str, optional): Specifies the type of memory. Currently, only
                `MemoryType.PROCEDURAL.value` ("procedural_memory") is explicitly handled for
                creating procedural memories (typically requires 'agent_id'). Otherwise, memories
                are treated as general conversational/factual memories.
            prompt (str, optional): Prompt to use for the memory creation. Defaults to None.


        Returns:
            dict: A dictionary containing the result of the memory addition operation, typically
                  including a list of memory items affected (added, updated) under a "results" key,
                  and potentially "relations" if graph store is enabled.
                  Example for v1.1+: `{"results": [{"id": "...", "memory": "...", "event": "ADD"}]}`
        """

        processed_metadata, effective_filters = _build_filters_and_metadata(
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            input_metadata=metadata,
        )

        if memory_type is not None and memory_type != MemoryType.PROCEDURAL.value:
            raise ValueError(
                f"Invalid 'memory_type'. Please pass {MemoryType.PROCEDURAL.value} to create procedural memories."
            )

        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        elif isinstance(messages, dict):
            messages = [messages]

        elif not isinstance(messages, list):
            raise ValueError("messages must be str, dict, or list[dict]")

        if agent_id is not None and memory_type == MemoryType.PROCEDURAL.value:
            results = self._create_procedural_memory(messages, metadata=processed_metadata, prompt=prompt)
            return results

        # Optimization: if infer=False (direct storage mode), skip vision processing for speed
        # Only process vision messages when inference is needed
        if not infer and self.config.mllm.config.get("enable_vision"):
            # When infer=False, use original messages directly without calling vision model (much faster)
            # For image URLs, store directly as text description
            processed_messages = []
            for msg in messages:
                if isinstance(msg.get("content"), dict) and msg["content"].get("type") == "image_url":
                    # For images, use file path as description without calling LLM
                    image_url = msg["content"]["image_url"]["url"]
                    processed_messages.append({
                        "role": msg["role"],
                        "content": f"Screenshot image: {os.path.basename(image_url)}"
                    })
                else:
                    processed_messages.append(msg)
            messages = processed_messages
        elif self.config.mllm.config.get("enable_vision"):
            messages = parse_vision_messages(messages, self.mllm, self.config.llm.config.get("vision_details"))
        else:
            messages = parse_vision_messages(messages)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future1 = executor.submit(self._add_to_vector_store, messages, processed_metadata, effective_filters, infer)
            future2 = executor.submit(self._add_to_graph, messages, effective_filters)

            concurrent.futures.wait([future1, future2])

            vector_store_result = future1.result()
            graph_result = future2.result()

        if self.api_version == "v1.0":
            warnings.warn(
                "The current add API output format is deprecated. "
                "To use the latest format, set `api_version='v1.1'`. "
                "The current format will be removed in MemScreen 1.0.0 and later versions.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return vector_store_result

        if self.enable_graph:
            return {
                "results": vector_store_result,
                "relations": graph_result,
            }

        return {"results": vector_store_result}

    def _add_to_vector_store(self, messages, metadata, filters, infer):
        """Add messages to the vector store."""
        if not infer:
            returned_memories = []
            for message_dict in messages:
                if (
                    not isinstance(message_dict, dict)
                    or message_dict.get("role") is None
                    or message_dict.get("content") is None
                ):
                    logger.warning(f"Skipping invalid message format: {message_dict}")
                    continue

                if message_dict["role"] == "system":
                    continue

                per_msg_meta = deepcopy(metadata)
                per_msg_meta["role"] = message_dict["role"]

                actor_name = message_dict.get("name")
                if actor_name:
                    per_msg_meta["actor_id"] = actor_name

                msg_content = message_dict["content"]
                msg_embeddings = self.embedding_model.embed(msg_content, "add")
                mem_id = self._create_memory(msg_content, msg_embeddings, per_msg_meta)

                returned_memories.append(
                    {
                        "id": mem_id,
                        "memory": msg_content,
                        "event": "ADD",
                        "actor_id": actor_name if actor_name else None,
                        "role": message_dict["role"],
                    }
                )
            return returned_memories

        parsed_messages = parse_messages(messages)

        # OPTIMIZATION: Skip fact extraction for simple/short messages
        # This significantly improves speed for simple queries and short messages
        message_length = len(parsed_messages)
        should_skip_extraction = (
            message_length < 50 or  # Very short messages
            len(parsed_messages.split('\n')) < 2 or  # Single line messages
            # OPTIMIZATION: Also skip for commands/questions
            any(parsed_messages.strip().startswith(prefix) for prefix in ['!', '?', '/', 'http'])
        )

        if should_skip_extraction:
            logger.debug("Skipping fact extraction for simple message (speed optimization)")
            # Directly add the message as a memory
            returned_memories = []
            for message_dict in messages:
                if (
                    not isinstance(message_dict, dict)
                    or message_dict.get("role") is None
                    or message_dict.get("content") is None
                ):
                    continue

                if message_dict["role"] == "system":
                    continue

                per_msg_meta = deepcopy(metadata)
                per_msg_meta["role"] = message_dict["role"]

                actor_name = message_dict.get("name")
                if actor_name:
                    per_msg_meta["actor_id"] = actor_name

                msg_content = message_dict["content"]
                msg_embeddings = self.embedding_model.embed(msg_content, "add")
                mem_id = self._create_memory(msg_content, {msg_content: msg_embeddings}, per_msg_meta)

                returned_memories.append(
                    {
                        "id": mem_id,
                        "memory": msg_content,
                        "event": "ADD",
                        "actor_id": actor_name if actor_name else None,
                        "role": message_dict["role"],
                    }
                )
            return returned_memories

        # Build LLM request prompt
        if self.config.custom_fact_extraction_prompt:
            system_prompt = self.config.custom_fact_extraction_prompt
            user_prompt = f"Input:\n{parsed_messages}"
        else:
            system_prompt, user_prompt = get_fact_retrieval_messages(parsed_messages)

        # OPTIMIZATION: Use faster LLM parameters for fact extraction
        response = self.llm.generate_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            # OPTIMIZATION: Limit tokens for faster response
            options={
                "num_predict": 256,  # Limit output tokens
                "temperature": 0.3,  # Lower temperature for faster, focused output
                "top_p": 0.8,  # Slightly lower for faster sampling
            }
        )

        new_retrieved_facts = []
        try:
            # Clean LLM response for robust JSON parsing
            if isinstance(response, str):
                # Remove Ollama signature separators
                if '\n\n' in response:
                    response = response.split('\n\n')[-1]
                # Remove code block markers
                response = remove_code_blocks(response)
                # Clean whitespace
                response = response.strip().replace('\n','').replace('\t','')

            # Clean response to handle common LLM JSON formatting issues
            cleaned_response = response.strip()

            # Remove trailing quotes that LLM sometimes adds
            if cleaned_response.endswith('"'):
                # Check if it's an extra quote (not part of the JSON)
                try:
                    # Try parsing with the trailing quote removed
                    test_parse = json.loads(cleaned_response[:-1])
                    cleaned_response = cleaned_response[:-1]
                except:
                    pass

            # Parse JSON with fallback to Python dict extraction
            try:
                resp_dict = json.loads(cleaned_response)
            except:
                resp_dict = extract_python_dict(cleaned_response)

            # Extract facts safely with None check
            if resp_dict is None:
                logger.warning("JSON parsing returned None, using empty facts list")
                resp_dict = {}

            new_retrieved_facts = resp_dict.get("facts", [])
            if not isinstance(new_retrieved_facts, list):
                new_retrieved_facts = []

        except Exception as e:
            logger.error(
                f"Failed to parse extracted facts from LLM response: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            logger.error(f"Raw LLM response: {response}")
            new_retrieved_facts = []

        if not new_retrieved_facts:
            logger.debug("No new facts retrieved from input. Skipping memory update LLM call.")

        # OPTIMIZATION: Batch embedding generation and vector search for better performance
        retrieved_old_memory = []
        new_message_embeddings = {}

        # Filter valid facts
        valid_facts = [new_mem for new_mem in new_retrieved_facts
                      if isinstance(new_mem, str) and len(new_mem.strip()) > 0]

        if valid_facts:
            # OPTIMIZATION: Batch generate embeddings for all facts at once
            # This is much faster than generating one by one
            try:
                # Try batch embedding if the embedder supports it
                if hasattr(self.embedding_model, 'embed_batch'):
                    embeddings_list = self.embedding_model.embed_batch(valid_facts, "add")
                else:
                    # Fallback to individual embedding with list comprehension
                    embeddings_list = [self.embedding_model.embed(fact, "add") for fact in valid_facts]

                # Store embeddings for later use
                for fact, embedding in zip(valid_facts, embeddings_list):
                    new_message_embeddings[fact] = embedding

                # OPTIMIZATION: Batch search - collect all results at once
                # Instead of searching per fact, we search once per fact but process in parallel
                def search_single_fact(fact_emb_tuple):
                    fact, emb = fact_emb_tuple
                    memories = self.vector_store.search(
                        query=fact,
                        vectors=emb,
                        limit=5,
                        filters=filters,
                    )
                    return [{"id": mem.id, "text": mem.payload["data"]}
                           for mem in memories
                           if hasattr(mem, "id") and hasattr(mem, "payload") and mem.payload.get("data")]

                # Use ThreadPoolExecutor for parallel searches
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    search_results = list(executor.map(search_single_fact, new_message_embeddings.items()))

                # Flatten results
                for results in search_results:
                    retrieved_old_memory.extend(results)

            except Exception as e:
                logger.error(f"Batch embedding/search failed: {e}, falling back to sequential")
                # Fallback to original sequential method
                for new_mem in valid_facts:
                    messages_embeddings = self.embedding_model.embed(new_mem, "add")
                    new_message_embeddings[new_mem] = messages_embeddings

                    existing_memories = self.vector_store.search(
                        query=new_mem,
                        vectors=messages_embeddings,
                        limit=5,
                        filters=filters,
                    )

                    for mem in existing_memories:
                        if hasattr(mem, "id") and hasattr(mem, "payload") and mem.payload.get("data"):
                            retrieved_old_memory.append({"id": mem.id, "text": mem.payload["data"]})

        # Deduplicate memories by ID
        unique_data = {item["id"]: item for item in retrieved_old_memory}
        retrieved_old_memory = list(unique_data.values())
        logger.info(f"Total existing memories after deduplication: {len(retrieved_old_memory)}")

        # Create UUID mapping to handle LLM hallucinations
        # LLM may return UUIDs that don't exist, so we map numeric indices to real UUIDs
        temp_uuid_mapping = {}
        for idx, item in enumerate(retrieved_old_memory):
            temp_uuid_mapping[str(idx)] = item["id"]
            retrieved_old_memory[idx]["id"] = str(idx)

        # Determine which memories to ADD, UPDATE, or DELETE
        new_memories_with_actions = {}

        if new_retrieved_facts:
            function_calling_prompt = get_update_memory_messages(
                retrieved_old_memory, new_retrieved_facts, self.config.custom_update_memory_prompt
            )
            response = ""

            try:
                # OPTIMIZATION: Use faster parameters for memory update
                response = self.llm.generate_response(
                    messages=[{"role": "user", "content": function_calling_prompt}],
                    response_format={"type": "json_object"},
                    options={
                        "num_predict": 512,  # Limit output for speed
                        "temperature": 0.3,   # Lower temperature
                        "top_p": 0.8,
                    }
                )

                # Clean response for parsing
                if isinstance(response, str) and '\n\n' in response:
                    response = response.split('\n\n')[-1]
                response = remove_code_blocks(response).strip().replace('\n','').replace('\t','')

                # Parse JSON with fallback
                try:
                    new_memories_with_actions = json.loads(response)
                except:
                    new_memories_with_actions = extract_json_from_response(response) or {}

            except Exception as e:
                logger.error(f"Failed to generate update memory response: {type(e).__name__}: {str(e)}", exc_info=True)
                new_memories_with_actions = {}

        # Execute memory actions
        returned_memories = []

        try:
            # Extract memory actions from response
            memory_actions = []
            if isinstance(new_memories_with_actions, list):
                memory_actions = new_memories_with_actions
            elif isinstance(new_memories_with_actions, dict):
                memory_actions = new_memories_with_actions.get("memory", [])
            else:
                memory_actions = []

            # Process each memory action
            for resp in memory_actions:
                if not isinstance(resp, dict):
                    continue

                logger.info(f"Processing memory action: {resp}")
                action_text = resp.get("text", "").strip()
                event_type = resp.get("event", "").upper()

                # Validate action text
                if not action_text:
                    logger.warning("Skipping memory entry: empty `text` field.")
                    continue

                # Validate event type
                if event_type not in ["ADD", "UPDATE", "DELETE", "NONE"]:
                    logger.warning(f"Skipping invalid event type: {event_type} | content: {resp}")
                    continue

                # Handle UUID hallucinations: if LLM returns non-existent UUID, convert to ADD
                mem_id = resp.get("id")
                if mem_id not in temp_uuid_mapping and event_type in ["UPDATE", "DELETE"]:
                    logger.warning(f"UUID hallucination detected, converting {event_type} -> ADD | id: {mem_id}")
                    event_type = "ADD"

                # Execute the memory action
                try:
                    if event_type == "ADD":
                        memory_id = self._create_memory(
                            data=action_text,
                            existing_embeddings=new_message_embeddings,
                            metadata=metadata,
                        )
                        returned_memories.append({"id": memory_id, "memory": action_text, "event": event_type})

                    elif event_type == "UPDATE":
                        real_mem_id = temp_uuid_mapping.get(mem_id)
                        self._update_memory(
                            memory_id=real_mem_id,
                            data=action_text,
                            existing_embeddings=new_message_embeddings,
                            metadata=metadata,
                        )
                        returned_memories.append(
                            {
                                "id": real_mem_id,
                                "memory": action_text,
                                "event": event_type,
                                "previous_memory": resp.get("old_memory"),
                            }
                        )

                    elif event_type == "DELETE":
                        real_mem_id = temp_uuid_mapping.get(mem_id)
                        self._delete_memory(memory_id=real_mem_id)
                        returned_memories.append(
                            {
                                "id": real_mem_id,
                                "memory": action_text,
                                "event": event_type,
                            }
                        )
                    elif event_type == "NONE":
                        logger.info("Memory action: NOOP (no operation)")

                except Exception as e:
                    logger.error(f"Failed to process memory action: {resp} | error: {type(e).__name__}: {str(e)}", exc_info=True)

        except Exception as e:
            logger.error(f"Failed to iterate memory actions: {type(e).__name__}: {str(e)}", exc_info=True)

        keys, encoded_ids = process_telemetry_filters(filters)
        capture_event(
            "memscreen.add",
            self,
            {"version": self.api_version, "keys": keys, "encoded_ids": encoded_ids, "sync_type": "sync"},
        )
        return returned_memories

    def _add_to_graph(self, messages, filters):
        """Add messages to the graph store by extracting entities and relationships."""
        added_entities = []

        if self.enable_graph and self.graph:
            try:
                if filters.get("user_id") is None:
                    filters["user_id"] = "user"

                # Combine message content
                data = "\n".join([msg["content"] for msg in messages if "content" in msg and msg["role"] != "system"])

                # Extract entities and relationships using LLM
                nodes, edges = self.entity_extractor.extract_entities_and_relations(
                    data,
                    user_id=filters.get("user_id")
                )

                # Add nodes to graph
                node_ids = {}
                for node in nodes:
                    node_id = self.graph.add_node(node)
                    node_ids[node.label] = node_id

                # Add edges to graph (map entity names to node IDs)
                for edge in edges:
                    # Map source and target names to node IDs
                    if edge.source in node_ids:
                        edge.source = node_ids[edge.source]
                    if edge.target in node_ids:
                        edge.target = node_ids[edge.target]

                    # Only add edge if both nodes exist
                    if edge.source in node_ids.values() and edge.target in node_ids.values():
                        self.graph.add_edge(edge)

                added_entities = [{"nodes": len(nodes), "edges": len(edges)}]
                logger.info(f"Added {len(nodes)} entities and {len(edges)} relationships to graph")

            except Exception as e:
                logger.error(f"Failed to add to graph: {e}")
                import traceback
                traceback.print_exc()

        return added_entities

    def get(self, memory_id):
        """
        Retrieve a memory by ID.

        Args:
            memory_id (str): ID of the memory to retrieve.

        Returns:
            dict: Retrieved memory.
        """
        capture_event("memscreen.get", self, {"memory_id": memory_id, "sync_type": "sync"})
        memory = self.vector_store.get(vector_id=memory_id)
        if not memory:
            return None

        promoted_payload_keys = [
            "user_id",
            "agent_id",
            "run_id",
            "actor_id",
            "role",
        ]

        core_and_promoted_keys = {"data", "hash", "created_at", "updated_at", "id", *promoted_payload_keys}

        result_item = MemoryItem(
            id=memory.id,
            memory=memory.payload["data"],
            hash=memory.payload.get("hash"),
            created_at=memory.payload.get("created_at"),
            updated_at=memory.payload.get("updated_at"),
        ).model_dump()

        for key in promoted_payload_keys:
            if key in memory.payload:
                result_item[key] = memory.payload[key]

        additional_metadata = {k: v for k, v in memory.payload.items() if k not in core_and_promoted_keys}
        if additional_metadata:
            result_item["metadata"] = additional_metadata

        return result_item

    def get_all(
        self,
        *,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ):
        """
        List all memories.

        Args:
            user_id (str, optional): user id
            agent_id (str, optional): agent id
            run_id (str, optional): run id
            filters (dict, optional): Additional custom key-value filters to apply to the search.
                These are merged with the ID-based scoping filters. For example,
                `filters={"actor_id": "some_user"}`.
            limit (int, optional): The maximum number of memories to return. Defaults to 100.

        Returns:
            dict: A dictionary containing a list of memories under the "results" key,
                  and potentially "relations" if graph store is enabled. For API v1.0,
                  it might return a direct list (see deprecation warning).
                  Example for v1.1+: `{"results": [{"id": "...", "memory": "...", ...}]}`
        """

        _, effective_filters = _build_filters_and_metadata(
            user_id=user_id, agent_id=agent_id, run_id=run_id, input_filters=filters
        )

        if not any(key in effective_filters for key in ("user_id", "agent_id", "run_id")):
            raise ValueError("At least one of 'user_id', 'agent_id', or 'run_id' must be specified.")

        keys, encoded_ids = process_telemetry_filters(effective_filters)
        capture_event(
            "memscreen.get_all", self, {"limit": limit, "keys": keys, "encoded_ids": encoded_ids, "sync_type": "sync"}
        )

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_memories = executor.submit(self._get_all_from_vector_store, effective_filters, limit)
            future_graph_entities = (
                executor.submit(self.graph.get_all, effective_filters, limit) if self.enable_graph else None
            )

            concurrent.futures.wait(
                [future_memories, future_graph_entities] if future_graph_entities else [future_memories]
            )

            all_memories_result = future_memories.result()
            graph_entities_result = future_graph_entities.result() if future_graph_entities else None

        if self.enable_graph:
            return {"results": all_memories_result, "relations": graph_entities_result}

        if self.api_version == "v1.0":
            warnings.warn(
                "The current get_all API output format is deprecated. "
                "To use the latest format, set `api_version='v1.1'` (which returns a dict with a 'results' key). "
                "The current format (direct list for v1.0) will be removed in MemScreen 1.0.0 and later versions.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return all_memories_result
        else:
            return {"results": all_memories_result}

    def _get_all_from_vector_store(self, filters, limit):
        """Get all memories from vector store."""
        memories_result = self.vector_store.list(filters=filters, limit=limit)
        actual_memories = (
            memories_result[0]
            if isinstance(memories_result, (tuple, list)) and len(memories_result) > 0
            else memories_result
        )

        promoted_payload_keys = [
            "user_id",
            "agent_id",
            "run_id",
            "actor_id",
            "role",
        ]
        core_and_promoted_keys = {"data", "hash", "created_at", "updated_at", "id", *promoted_payload_keys}

        formatted_memories = []
        for mem in actual_memories:
            memory_item_dict = MemoryItem(
                id=mem.id,
                memory=mem.payload["data"],
                hash=mem.payload.get("hash"),
                created_at=mem.payload.get("created_at"),
                updated_at=mem.payload.get("updated_at"),
            ).model_dump(exclude={"score"})

            for key in promoted_payload_keys:
                if key in mem.payload:
                    memory_item_dict[key] = mem.payload[key]

            additional_metadata = {k: v for k, v in mem.payload.items() if k not in core_and_promoted_keys}
            if additional_metadata:
                memory_item_dict["metadata"] = additional_metadata

            formatted_memories.append(memory_item_dict)

        return formatted_memories

    def search(
        self,
        query: str,
        *,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        threshold: Optional[float] = None,
    ):
        """
        Searches for memories based on a query
        Args:
            query (str): Query to search for.
            user_id (str, optional): ID of the user to search for. Defaults to None.
            agent_id (str, optional): ID of the agent to search for. Defaults to None.
            run_id (str, optional): ID of the run to search for. Defaults to None.
            limit (int, optional): Limit the number of results. Defaults to 100.
            filters (dict, optional): Filters to apply to the search. Defaults to None..
            threshold (float, optional): Minimum score for a memory to be included in the results. Defaults to None.

        Returns:
            dict: A dictionary containing the search results, typically under a "results" key,
                  and potentially "relations" if graph store is enabled.
                  Example for v1.1+: `{"results": [{"id": "...", "memory": "...", "score": 0.8, ...}]}`
        """
        _, effective_filters = _build_filters_and_metadata(
            user_id=user_id, agent_id=agent_id, run_id=run_id, input_filters=filters
        )

        if not any(key in effective_filters for key in ("user_id", "agent_id", "run_id")):
            raise ValueError("At least one of 'user_id', 'agent_id', or 'run_id' must be specified.")

        keys, encoded_ids = process_telemetry_filters(effective_filters)
        capture_event(
            "memscreen.search",
            self,
            {
                "limit": limit,
                "version": self.api_version,
                "keys": keys,
                "encoded_ids": encoded_ids,
                "sync_type": "sync",
                "threshold": threshold,
            },
        )

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_memories = executor.submit(self._search_vector_store, query, effective_filters, limit, threshold)
            future_graph_entities = (
                executor.submit(self.graph.search, query, effective_filters, limit) if self.enable_graph else None
            )

            concurrent.futures.wait(
                [future_memories, future_graph_entities] if future_graph_entities else [future_memories]
            )

            original_memories = future_memories.result()
            graph_entities = future_graph_entities.result() if future_graph_entities else None

        if self.enable_graph:
            return {"results": original_memories, "relations": graph_entities}

        if self.api_version == "v1.0":
            warnings.warn(
                "The current search API output format is deprecated. "
                "To use the latest format, set `api_version='v1.1'`. "
                "The current format will be removed in MemScreen 1.0.0 and later versions.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return {"results": original_memories}
        else:
            return {"results": original_memories}

    def _search_vector_store(self, query, filters, limit, threshold: Optional[float] = None):
        """Search vector store for memories with intelligent caching."""
        # OPTIMIZATION: Check cache first before doing expensive vector search
        # Generate cache key from query, filters, limit
        cache_key = f"{query}:{str(sorted(filters.items()))}:{limit}"

        # Try to get from cache
        cached_result = _search_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for search query: {query[:50]}...")
            # Apply threshold filter if needed
            if threshold is not None:
                cached_result = [m for m in cached_result if m.get("score", 0) >= threshold]
            return cached_result

        # Cache miss - perform actual search
        logger.debug(f"Cache miss for search query: {query[:50]}...")
        embeddings = self.embedding_model.embed(query, "search")
        memories = self.vector_store.search(query=query, vectors=embeddings, limit=limit, filters=filters)

        promoted_payload_keys = [
            "user_id",
            "agent_id",
            "run_id",
            "actor_id",
            "role",
        ]

        core_and_promoted_keys = {"data", "hash", "created_at", "updated_at", "id", *promoted_payload_keys}

        original_memories = []
        for mem in memories:
            memory_item_dict = MemoryItem(
                id=mem.id,
                memory=mem.payload["data"],
                hash=mem.payload.get("hash"),
                created_at=mem.payload.get("created_at"),
                updated_at=mem.payload.get("updated_at"),
                score=mem.score,
            ).model_dump()

            for key in promoted_payload_keys:
                if key in mem.payload:
                    memory_item_dict[key] = mem.payload[key]

            additional_metadata = {k: v for k, v in mem.payload.items() if k not in core_and_promoted_keys}
            if additional_metadata:
                memory_item_dict["metadata"] = additional_metadata

            if threshold is None or mem.score >= threshold:
                original_memories.append(memory_item_dict)

        # OPTIMIZATION: Store results in cache for future queries
        # Cache the results before threshold filtering (more reusable)
        _search_cache.set(cache_key, original_memories)

        # Periodic cache cleanup (every 100 searches)
        import random
        if random.random() < 0.01:  # 1% chance to cleanup
            expired = _search_cache.cleanup_expired()
            if expired > 0:
                logger.debug(f"Cleaned up {expired} expired cache entries")

        return original_memories

    def update(self, memory_id, data):
        """
        Update a memory by ID.

        Args:
            memory_id (str): ID of the memory to update.
            data (dict): Data to update the memory with.

        Returns:
            dict: Updated memory.
        """
        capture_event("memscreen.update", self, {"memory_id": memory_id, "sync_type": "sync"})

        existing_embeddings = {data: self.embedding_model.embed(data, "update")}

        self._update_memory(memory_id, data, existing_embeddings)
        return {"message": "Memory updated successfully!"}

    def delete(self, memory_id):
        """
        Delete a memory by ID.

        Args:
            memory_id (str): ID of the memory to delete.
        """
        capture_event("memscreen.delete", self, {"memory_id": memory_id, "sync_type": "sync"})
        self._delete_memory(memory_id)
        return {"message": "Memory deleted successfully!"}

    def delete_all(self, user_id: Optional[str] = None, agent_id: Optional[str] = None, run_id: Optional[str] = None):
        """
        Delete all memories.

        Args:
            user_id (str, optional): ID of the user to delete memories for. Defaults to None.
            agent_id (str, optional): ID of the agent to delete memories for. Defaults to None.
            run_id (str, optional): ID of the run to delete memories for. Defaults to None.
        """
        filters: Dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if agent_id:
            filters["agent_id"] = agent_id
        if run_id:
            filters["run_id"] = run_id

        if not filters:
            raise ValueError(
                "At least one filter is required to delete all memories. If you want to delete all memories, use the `reset()` method."
            )

        keys, encoded_ids = process_telemetry_filters(filters)
        capture_event("memscreen.delete_all", self, {"keys": keys, "encoded_ids": encoded_ids, "sync_type": "sync"})
        memories = self.vector_store.list(filters=filters)[0]
        for memory in memories:
            self._delete_memory(memory.id)

        logger.info(f"Deleted {len(memories)} memories")

        if self.enable_graph:
            self.graph.delete_all(filters)

        return {"message": "Memories deleted successfully!"}

    def history(self, memory_id):
        """
        Get the history of changes for a memory by ID.

        Args:
            memory_id (str): ID of the memory to get history for.

        Returns:
            list: List of changes for the memory.
        """
        capture_event("memscreen.history", self, {"memory_id": memory_id, "sync_type": "sync"})
        return self.db.get_history(memory_id)

    def _create_memory(self, data, existing_embeddings, metadata=None):
        """Create a new memory."""
        logger.debug(f"Creating memory with {data=}")
        if data in existing_embeddings:
            embeddings = existing_embeddings[data]
        else:
            embeddings = self.embedding_model.embed(data, memory_action="add")
        memory_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata["data"] = data
        metadata["hash"] = hashlib.md5(data.encode()).hexdigest()

        import pytz
        metadata["created_at"] = datetime.now(pytz.timezone(self.config.timezone)).isoformat()

        self.vector_store.insert(
            vectors=[embeddings],
            ids=[memory_id],
            payloads=[metadata],
        )
        # OPTIMIZATION: Use batch database writing for better performance
        # Pass immediate=False to use batch writing (default behavior)
        self.db.add_history(
            memory_id,
            None,
            data,
            "ADD",
            created_at=metadata.get("created_at"),
            actor_id=metadata.get("actor_id"),
            role=metadata.get("role"),
            immediate=False,  # Use batch writing
        )
        capture_event("memscreen._create_memory", self, {"memory_id": memory_id, "sync_type": "sync"})
        return memory_id

    def _create_procedural_memory(self, messages, metadata=None, prompt=None):
        """
        Create a procedural memory

        Args:
            messages (list): List of messages to create a procedural memory from.
            metadata (dict): Metadata to create a procedural memory from.
            prompt (str, optional): Prompt to use for the procedural memory creation. Defaults to None.
        """
        logger.info("Creating procedural memory")

        parsed_messages = [
            {"role": "system", "content": prompt or PROCEDURAL_MEMORY_SYSTEM_PROMPT},
            *messages,
            {
                "role": "user",
                "content": "Create procedural memory of the above conversation.",
            },
        ]

        try:
            procedural_memory = self.llm.generate_response(messages=parsed_messages)
        except Exception as e:
            logger.error(f"Error generating procedural memory summary: {e}")
            raise

        if metadata is None:
            raise ValueError("Metadata cannot be done for procedural memory.")

        metadata["memory_type"] = MemoryType.PROCEDURAL.value
        embeddings = self.embedding_model.embed(procedural_memory, memory_action="add")
        memory_id = self._create_memory(procedural_memory, {procedural_memory: embeddings}, metadata=metadata)
        capture_event("memscreen._create_procedural_memory", self, {"memory_id": memory_id, "sync_type": "sync"})

        result = {"results": [{"id": memory_id, "memory": procedural_memory, "event": "ADD"}]}

        return result

    def _update_memory(self, memory_id, data, existing_embeddings, metadata=None):
        """Update an existing memory."""
        logger.info(f"Updating memory with {data=}")

        try:
            existing_memory = self.vector_store.get(vector_id=memory_id)
        except Exception:
            logger.error(f"Error getting memory with ID {memory_id} during update.")
            raise ValueError(f"Error getting memory with ID {memory_id}. Please provide a valid 'memory_id'")

        prev_value = existing_memory.payload.get("data")

        new_metadata = deepcopy(metadata) if metadata is not None else {}

        new_metadata["data"] = data
        new_metadata["hash"] = hashlib.md5(data.encode()).hexdigest()
        new_metadata["created_at"] = existing_memory.payload.get("created_at")

        import pytz
        new_metadata["updated_at"] = datetime.now(pytz.timezone(self.config.timezone)).isoformat()

        if "user_id" in existing_memory.payload:
            new_metadata["user_id"] = existing_memory.payload["user_id"]
        if "agent_id" in existing_memory.payload:
            new_metadata["agent_id"] = existing_memory.payload["agent_id"]
        if "run_id" in existing_memory.payload:
            new_metadata["run_id"] = existing_memory.payload["run_id"]
        if "actor_id" in existing_memory.payload:
            new_metadata["actor_id"] = existing_memory.payload["actor_id"]
        if "role" in existing_memory.payload:
            new_metadata["role"] = existing_memory.payload["role"]

        if data in existing_embeddings:
            embeddings = existing_embeddings[data]
        else:
            embeddings = self.embedding_model.embed(data, "update")

        self.vector_store.update(
            vector_id=memory_id,
            vector=embeddings,
            payload=new_metadata,
        )
        logger.info(f"Updating memory with ID {memory_id=} with {data=}")

        # OPTIMIZATION: Use batch database writing
        self.db.add_history(
            memory_id,
            prev_value,
            data,
            "UPDATE",
            created_at=new_metadata["created_at"],
            updated_at=new_metadata["updated_at"],
            actor_id=new_metadata.get("actor_id"),
            role=new_metadata.get("role"),
            immediate=False,  # Use batch writing
        )
        capture_event("memscreen._update_memory", self, {"memory_id": memory_id, "sync_type": "sync"})
        return memory_id

    def _delete_memory(self, memory_id):
        """Delete a memory."""
        logger.info(f"Deleting memory with {memory_id=}")
        existing_memory = self.vector_store.get(vector_id=memory_id)
        prev_value = existing_memory.payload["data"]
        self.vector_store.delete(vector_id=memory_id)
        # OPTIMIZATION: Use batch database writing
        # Delete operations are also batched, but we set immediate=True
        # for deletes as they're less frequent and more critical
        self.db.add_history(
            memory_id,
            prev_value,
            None,
            "DELETE",
            actor_id=existing_memory.payload.get("actor_id"),
            role=existing_memory.payload.get("role"),
            is_deleted=1,
            immediate=True,  # Deletes should be written immediately
        )
        capture_event("memscreen._delete_memory", self, {"memory_id": memory_id, "sync_type": "sync"})
        return memory_id

    def reset(self):
        """
        Reset the memory store by:
            Deletes the vector store collection
            Resets the database
            Recreates the vector store with a new client
        """
        logger.warning("Resetting all memories")

        if hasattr(self.db, "connection") and self.db.connection:
            self.db.connection.execute("DROP TABLE IF EXISTS history")
            self.db.connection.close()

        self.db = SQLiteManager(self.config.history_db_path)

        if hasattr(self.vector_store, "reset"):
            self.vector_store = VectorStoreFactory.reset(self.vector_store)
        else:
            logger.warning("Vector store does not support reset. Skipping.")
            self.vector_store.delete_col()
            self.vector_store = VectorStoreFactory.create(
                self.config.vector_store.provider, self.config.vector_store.config
            )
        capture_event("memscreen.reset", self, {"sync_type": "sync"})


__all__ = ["Memory", "_build_filters_and_metadata"]
