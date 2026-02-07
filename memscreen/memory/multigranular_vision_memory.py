### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Multigranular visual memory system (simplified implementation).

This module provides multi-level visual representation:
- Scene-Level: Overall description of the visual scene
- Text-Level: Extracted text content (OCR)

Note: This is a simplified implementation that uses existing vision models
rather than specialized object detectors. Future versions can integrate
YOLOv8n for object detection and EasyOCR for text extraction.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = [
    "MultigranularVisionMemory",
    "MultigranularMemoryConfig",
]


class MultigranularMemoryConfig:
    """
    Configuration for multigranular vision memory.

    Args:
        enable_scene_level: Enable scene-level descriptions
        enable_text_level: Enable text-level extraction
        scene_model: Vision model for scene description
    """

    def __init__(
        self,
        enable_scene_level: bool = True,
        enable_text_level: bool = True,
        scene_model: str = "qwen2.5vl:3b",
    ):
        self.enable_scene_level = enable_scene_level
        self.enable_text_level = enable_text_level
        self.scene_model = scene_model


class MultigranularVisionMemory:
    """
    Multi-granular visual memory system.

    Extracts and stores visual information at multiple granularities:
    - Scene level: High-level description (what application, what activity)
    - Text level: Text content visible in the image

    This simplified version uses the existing qwen2.5vl vision model
    for both scene description and text extraction.

    Example:
        ```python
        memory = MultigranularVisionMemory(
            vision_encoder=encoder,
            llm=llm
        )

        processed = memory.process_screenshot(
            image_path="screenshot.png",
            timestamp=datetime.now()
        )

        # Store in vector store
        memory.store_multigranular_memory(
            processed=processed,
            vector_store=store,
            memory_id="mem123"
        )
        ```
    """

    def __init__(
        self,
        vision_encoder,
        llm,
        config: Optional[MultigranularMemoryConfig] = None,
    ):
        """
        Initialize multigranular vision memory.

        Args:
            vision_encoder: Vision encoder for generating embeddings
            llm: LLM for generating scene descriptions
            config: Configuration options
        """
        if config is None:
            config = MultigranularMemoryConfig()

        self.vision_encoder = vision_encoder
        self.llm = llm
        self.config = config

        logger.info(
            f"MultigranularVisionMemory initialized "
            f"(scene={config.enable_scene_level}, text={config.enable_text_level})"
        )

    def process_screenshot(
        self,
        image_path: str,
        timestamp: datetime,
    ) -> Dict:
        """
        Process screenshot and extract multi-granular information.

        Args:
            image_path: Path to screenshot
            timestamp: Capture timestamp

        Returns:
            Processed data dict with:
            - image_path: str
            - timestamp: str
            - scene: Dict (scene-level data)
            - text: Dict (text-level data)
            - embeddings: Dict (all embeddings)
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        result = {
            'image_path': image_path,
            'timestamp': timestamp.isoformat(),
            'scene': {},
            'text': {},
            'embeddings': {},
        }

        # Scene-level extraction
        if self.config.enable_scene_level:
            scene_data = self._extract_scene_level(image_path)
            result['scene'] = scene_data

            # Generate scene embedding
            scene_embedding = self.vision_encoder.encode_image(image_path)
            result['embeddings']['scene'] = scene_embedding

        # Text-level extraction
        if self.config.enable_text_level:
            text_data = self._extract_text_level(image_path)
            result['text'] = text_data

        logger.info(
            f"Processed screenshot: {image_path} "
            f"(scene={bool(result['scene'])}, text={bool(result['text'])})"
        )

        return result

    def _extract_scene_level(self, image_path: str) -> Dict:
        """
        Extract scene-level description.

        Uses vision model to generate:
        - High-level description
        - Scene type classification

        Args:
            image_path: Path to image

        Returns:
            Scene data dict
        """
        try:
            # Prompt for scene description
            prompt = """Describe this screenshot focusing on:
1. What application is running?
2. What is the user doing?
3. What is the overall scene type (coding, browsing, document editing, etc.)?

Provide a concise one-sentence description followed by the scene type.
Format: [description] | [scene_type]"""

            # Use vision model to analyze image
            # TODO: This assumes the LLM supports vision
            # For now, return a basic description
            # In production, integrate with actual vision model

            # Placeholder implementation
            description = "Screenshot captured"
            scene_type = self._classify_scene_type_basic(image_path)

            return {
                'description': description,
                'scene_type': scene_type,
                'granularity': 'scene',
            }

        except Exception as e:
            logger.error(f"Scene extraction failed: {e}")
            return {
                'description': '',
                'scene_type': 'unknown',
                'granularity': 'scene',
            }

    def _extract_text_level(self, image_path: str) -> Dict:
        """
        Extract text content from image.

        In this simplified version, we rely on the vision model's
        built-in text recognition. Future versions can integrate
        specialized OCR engines like EasyOCR.

        Args:
            image_path: Path to image

        Returns:
            Text data dict
        """
        try:
            # Placeholder implementation
            # In production, use vision model or OCR to extract text

            return {
                'text_content': '',
                'text_blocks': [],
                'granularity': 'text',
            }

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                'text_content': '',
                'text_blocks': [],
                'granularity': 'text',
            }

    def _classify_scene_type_basic(self, image_path: str) -> str:
        """
        Basic scene type classification based on image path/properties.

        This is a simple heuristic-based classification.
        Production version should use actual vision model.

        Args:
            image_path: Path to image

        Returns:
            Scene type string
        """
        path_lower = image_path.lower()

        # Simple heuristics
        if 'code' in path_lower or 'ide' in path_lower:
            return 'coding'
        elif 'browser' in path_lower or 'web' in path_lower:
            return 'browsing'
        elif 'doc' in path_lower or 'pdf' in path_lower or 'word' in path_lower:
            return 'document_editing'
        elif 'terminal' in path_lower or 'console' in path_lower:
            return 'terminal'
        else:
            return 'general'

    def store_multigranular_memory(
        self,
        processed: Dict,
        vector_store,
        memory_id: str,
    ):
        """
        Store multigranular memory in vector store.

        Args:
            processed: Processed data from process_screenshot()
            vector_store: Multimodal vector store
            memory_id: Memory ID
        """
        # Store scene-level
        if processed.get('scene') and processed['embeddings'].get('scene'):
            scene_payload = {
                'granularity': 'scene',
                'description': processed['scene'].get('description', ''),
                'scene_type': processed['scene'].get('scene_type', ''),
                'timestamp': processed['timestamp'],
                'image_path': processed['image_path'],
                'memory_id': memory_id,
            }

            vector_store.insert_multimodal(
                ids=[f"{memory_id}_scene"],
                vision_embeddings=[processed['embeddings']['scene']],
                payloads=[scene_payload],
            )

        # Store text-level
        if processed.get('text'):
            text_content = processed['text'].get('text_content', '')
            if text_content:
                # TODO: Generate text embedding when needed
                text_payload = {
                    'granularity': 'text',
                    'text_content': text_content,
                    'text_blocks': processed['text'].get('text_blocks', []),
                    'timestamp': processed['timestamp'],
                    'memory_id': memory_id,
                }

                # For now, just store metadata without text embedding
                # Text embedding can be generated when text_embedder is available

        logger.info(f"Stored multigranular memory for {memory_id[:8]}")

    # Placeholder interfaces for future expansion
    def set_object_detector(self, detector):
        """
        Set object detector (future expansion).

        Args:
            detector: Object detector instance (e.g., YOLOv8n)
        """
        logger.warning("Object detector not yet implemented")
        pass

    def set_ocr_engine(self, ocr_engine):
        """
        Set OCR engine (future expansion).

        Args:
            ocr_engine: OCR engine instance (e.g., EasyOCR)
        """
        logger.warning("OCR engine not yet implemented")
        pass
