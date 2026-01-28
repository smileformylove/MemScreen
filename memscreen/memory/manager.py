"""
Unified Memory Manager for MemScreen
Coordinates memory operations across recording, OCR, and chat
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
from collections import defaultdict


class MemoryManager:
    """
    Centralized memory management for MemScreen

    Handles:
    - Screen recording memories
    - OCR text extraction
    - Chat conversations
    - Unified search and retrieval
    """

    def __init__(self, memory_system=None):
        """
        Initialize Memory Manager

        Args:
            memory_system: MemScreen Memory system instance
        """
        self.memory_system = memory_system

        # Memory type constants
        self.MEMORY_TYPES = {
            "RECORDING": "screen_recording",
            "OCR_TEXT": "ocr_text",
            "CHAT": "ai_chat",
            "USER_INFO": "user_info",
            "PREFERENCE": "user_preference"
        }

        # Statistics
        self.stats = {
            "recordings_saved": 0,
            "ocr_texts_saved": 0,
            "chats_saved": 0,
            "searches_performed": 0,
            "cache_hits": 0
        }

        # Simple cache for recent searches
        self.search_cache = {}
        self.cache_lock = threading.Lock()

    def save_recording(self, filename: str, frame_count: int, fps: float,
                       ocr_text: str = "", content_summary: str = "") -> bool:
        """
        Save screen recording to memory with OCR text

        Args:
            filename: Video file path
            frame_count: Number of frames
            fps: Frames per second
            ocr_text: Extracted text from OCR
            content_summary: Summary of content

        Returns:
            bool: Success status
        """
        if not self.memory_system:
            return False

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            duration = frame_count / fps if fps > 0 else 0

            # Build comprehensive memory entry
            memory_content = f"""Screen Recording ({timestamp}):
- Duration: {duration:.1f} seconds
- Frames: {frame_count}
- File: {filename}

OCR Extracted Text:
{ocr_text if ocr_text else "No text detected"}

Content Summary:
{content_summary if content_summary else "Screen recording captured"}

This recording shows what was on screen and can be used to answer questions about user activities."""

            # Add to memory with rich metadata
            result = self.memory_system.add(
                [{"role": "user", "content": memory_content}],
                user_id="default_user",
                metadata={
                    "type": self.MEMORY_TYPES["RECORDING"],
                    "filename": filename,
                    "frame_count": frame_count,
                    "fps": fps,
                    "duration": duration,
                    "timestamp": timestamp,
                    "has_ocr": bool(ocr_text),
                    "ocr_text": ocr_text[:500] if ocr_text else "",  # First 500 chars
                    "content_summary": content_summary
                },
                infer=False  # Don't use LLM for recordings (faster)
            )

            self.stats["recordings_saved"] += 1
            print(f"[MemoryManager] Saved recording: {filename} ({duration:.1f}s)")
            return True

        except Exception as e:
            print(f"[MemoryManager] Failed to save recording: {e}")
            return False

    def save_chat_conversation(self, user_message: str, ai_response: str,
                             model: str = "qwen3:1.7b", context: str = "") -> bool:
        """
        Save chat conversation to memory

        Args:
            user_message: User's message
            ai_response: AI's response
            model: Model used
            context: Additional context

        Returns:
            bool: Success status
        """
        if not self.memory_system:
            return False

        try:
            conversation = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ]

            result = self.memory_system.add(
                conversation,
                user_id="default_user",
                metadata={
                    "type": self.MEMORY_TYPES["CHAT"],
                    "timestamp": datetime.now().isoformat(),
                    "model": model,
                    "has_context": bool(context)
                },
                infer=True  # Use LLM to extract key facts
            )

            self.stats["chats_saved"] += 1
            print(f"[MemoryManager] Saved chat conversation")
            return True

        except Exception as e:
            print(f"[MemoryManager] Failed to save chat: {e}")
            return False

    def search_memories(self, query: str, limit: int = 5,
                       memory_types: Optional[List[str]] = None,
                       use_cache: bool = True) -> Dict:
        """
        Search memories with caching and filtering

        Args:
            query: Search query
            limit: Max results
            memory_types: Filter by memory types
            use_cache: Use search cache

        Returns:
            Dict: Search results
        """
        if not self.memory_system:
            return {"results": []}

        # Check cache
        cache_key = f"{query}_{limit}_{memory_types}"
        if use_cache:
            with self.cache_lock:
                if cache_key in self.search_cache:
                    self.stats["cache_hits"] += 1
                    return self.search_cache[cache_key]

        try:
            # Perform search
            result = self.memory_system.search(
                query=query,
                user_id="default_user",
                limit=limit,
                threshold=0.0  # Get all relevant results
            )

            # Filter by memory type if specified
            if memory_types and result and "results" in result:
                filtered = []
                for memory in result["results"]:
                    memory_meta = memory.get("metadata", {})
                    memory_type = memory_meta.get("type", "")
                    if memory_type in memory_types:
                        filtered.append(memory)
                result["results"] = filtered

            # Cache result
            if use_cache and result:
                with self.cache_lock:
                    self.search_cache[cache_key] = result
                    # Keep cache size manageable
                    if len(self.search_cache) > 100:
                        self.search_cache.clear()

            self.stats["searches_performed"] += 1
            return result

        except Exception as e:
            print(f"[MemoryManager] Search failed: {e}")
            return {"results": []}

    def get_chat_context(self, query: str, max_results: int = 3) -> str:
        """
        Get relevant context from memories for chat

        Args:
            query: Current user query
            max_results: Max memory results to include

        Returns:
            str: Formatted context string
        """
        result = self.search_memories(
            query=query,
            limit=max_results,
            memory_types=[
                self.MEMORY_TYPES["CHAT"],
                self.MEMORY_TYPES["RECORDING"],
                self.MEMORY_TYPES["OCR_TEXT"]
            ]
        )

        if not result or "results" not in result:
            return ""

        memories = result["results"]
        if not memories or len(memories) == 0:
            return ""

        # Build context from memories
        context_parts = []
        for mem in memories[:max_results]:
            if isinstance(mem, dict):
                if "memory" in mem:
                    content = mem["memory"]
                elif "content" in mem:
                    content = mem["content"]
                else:
                    content = str(mem)

                # Add metadata info
                memory_meta = mem.get("metadata", {})
                memory_type = memory_meta.get("type", "unknown")
                timestamp = memory_meta.get("timestamp", "")

                context_parts.append(f"[{memory_type}] {content}")

        if context_parts:
            return "Relevant context from memory:\n" + "\n".join(context_parts)

        return ""

    def get_user_activities_summary(self, limit: int = 10) -> str:
        """
        Get summary of recent user activities

        Args:
            limit: Max activities to summarize

        Returns:
            str: Summary of activities
        """
        result = self.search_memories(
            query="user activities recordings screenshots",
            limit=limit,
            memory_types=[self.MEMORY_TYPES["RECORDING"]]
        )

        if not result or "results" not in result:
            return "No recent activities recorded."

        memories = result["results"]
        if not memories:
            return "No recent activities recorded."

        summary_parts = []
        for mem in memories:
            if isinstance(mem, dict):
                meta = mem.get("metadata", {})
                timestamp = meta.get("timestamp", "Unknown time")
                duration = meta.get("duration", 0)
                has_text = meta.get("has_ocr", False)

                summary = f"- {timestamp}: "
                if duration:
                    summary += f"{duration:.1f}s recording"
                if has_text:
                    summary += " (with text)"
                summary_parts.append(summary)

        return "Recent activities:\n" + "\n".join(summary_parts)

    def optimize_memory_storage(self):
        """
        Optimize memory storage by cleaning duplicates and compressing
        """
        if not self.memory_system:
            return

        print("[MemoryManager] Memory optimization not yet implemented")
        # TODO: Implement memory cleanup, deduplication, compression

    def get_statistics(self) -> Dict:
        """Get memory usage statistics"""
        return self.stats.copy()

    def print_statistics(self):
        """Print memory statistics"""
        print("\n" + "="*60)
        print("📊 Memory Manager Statistics")
        print("="*60)
        print(f"Recordings Saved: {self.stats['recordings_saved']}")
        print(f"Chat Conversations: {self.stats['chats_saved']}")
        print(f"Searches Performed: {self.stats['searches_performed']}")
        print(f"Cache Hits: {self.stats['cache_hits']}")
        print(f"Cache Size: {len(self.search_cache)}")

        if self.stats['searches_performed'] > 0:
            hit_rate = self.stats['cache_hits'] / self.stats['searches_performed']
            print(f"Cache Hit Rate: {hit_rate:.1%}")

        print("="*60 + "\n")


# Global memory manager instance
_memory_manager = None


def get_memory_manager(memory_system=None) -> MemoryManager:
    """Get global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(memory_system)
    return _memory_manager


def reset_memory_manager():
    """Reset memory manager (for testing)"""
    global _memory_manager
    _memory_manager = None
