### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Unit and integration tests for hybrid vision-text retrieval system.

Tests the VisionEncoder, MultimodalChromaDB, and HybridVisionRetriever.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from PIL import Image


class TestVisionEncoder(unittest.TestCase):
    """Test VisionEncoder functionality."""

    def setUp(self):
        """Set up test fixtures."""
        from memscreen.embeddings.vision_encoder import VisionEncoderConfig, VisionEncoder

        self.config = VisionEncoderConfig(
            model_type="clip",  # Use CLIP for faster testing
            cache_size=10,
        )
        self.encoder = VisionEncoder(self.config)

        # Create temporary directory for test images
        self.test_dir = tempfile.mkdtemp()

        # Create a simple test image
        self.test_image_path = Path(self.test_dir) / "test_image.png"
        self._create_test_image(self.test_image_path)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
        self.encoder.clear_cache()

    def _create_test_image(self, path):
        """Create a simple test image."""
        img = Image.new('RGB', (100, 100), color='red')
        img.save(path)

    def test_vision_encoder_initialization(self):
        """Test VisionEncoder initializes correctly."""
        self.assertEqual(self.encoder.config.model_type, "clip")
        self.assertEqual(self.encoder.config.embedding_dims, 512)
        self.assertFalse(self.encoder._model_loaded)  # Lazy loading

    @unittest.skip("Requires sentence-transformers - skip for CI")
    def test_encode_image(self):
        """Test encoding a single image."""
        embedding = self.encoder.encode_image(str(self.test_image_path))

        # Check embedding dimensions
        self.assertEqual(len(embedding), 512)

        # Check all values are floats
        self.assertTrue(all(isinstance(x, float) for x in embedding))

    @unittest.skip("Requires sentence-transformers - skip for CI")
    def test_encode_image_returns_list(self):
        """Test encode_image returns list by default."""
        embedding = self.encoder.encode_image(str(self.test_image_path))
        self.assertIsInstance(embedding, list)

    @unittest.skip("Requires sentence-transformers - skip for CI")
    def test_encode_image_with_cache(self):
        """Test that caching works."""
        # First call
        embedding1 = self.encoder.encode_image(
            str(self.test_image_path),
            use_cache=True
        )

        # Second call should use cache
        embedding2 = self.encoder.encode_image(
            str(self.test_image_path),
            use_cache=True
        )

        # Should be identical
        self.assertEqual(embedding1, embedding2)

        # Cache should have 1 item
        stats = self.encoder.get_cache_stats()
        self.assertEqual(stats["size"], 1)

    @unittest.skip("Requires sentence-transformers - skip for CI")
    def test_compute_visual_hash(self):
        """Test perceptual hashing."""
        hash1 = self.encoder.compute_visual_hash(str(self.test_image_path))

        # Hash should be a string
        self.assertIsInstance(hash1, str)

        # Same image should produce same hash
        hash2 = self.encoder.compute_visual_hash(str(self.test_image_path))
        self.assertEqual(hash1, hash2)

    @unittest.skip("Requires sentence-transformers - skip for CI")
    def test_extract_visual_features(self):
        """Test low-level feature extraction."""
        features = self.encoder.extract_visual_features(str(self.test_image_path))

        # Check required fields
        self.assertIn("dominant_colors", features)
        self.assertIn("brightness", features)
        self.assertIn("contrast", features)
        self.assertIn("aspect_ratio", features)
        self.assertIn("layout_density", features)

        # Check value types and ranges
        self.assertIsInstance(features["brightness"], float)
        self.assertIsInstance(features["aspect_ratio"], float)
        self.assertGreater(features["aspect_ratio"], 0)

    @unittest.skip("Requires sentence-transformers - skip for CI")
    def test_clear_cache(self):
        """Test cache clearing."""
        # Add something to cache
        self.encoder.encode_image(str(self.test_image_path), use_cache=True)

        # Clear cache
        self.encoder.clear_cache()

        # Cache should be empty
        stats = self.encoder.get_cache_stats()
        self.assertEqual(stats["size"], 0)


class TestMultimodalChromaDB(unittest.TestCase):
    """Test MultimodalChromaDB functionality."""

    def setUp(self):
        """Set up test fixtures."""
        from memscreen.vector_store.multimodal_chroma import MultimodalChromaDB

        # Create temporary directory for test database
        self.test_db_dir = tempfile.mkdtemp()

        # Initialize store
        self.store = MultimodalChromaDB(
            collection_name="test_multimodal",
            text_embedding_dims=512,
            vision_embedding_dims=768,
            path=self.test_db_dir,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.store.reset()
        shutil.rmtree(self.test_db_dir)

    def test_initialization(self):
        """Test store initializes correctly."""
        self.assertIsNotNone(self.store.text_store)
        self.assertIsNotNone(self.store.vision_store)
        self.assertEqual(self.store.text_embedding_dims, 512)
        self.assertEqual(self.store.vision_embedding_dims, 768)

    def test_insert_text_only(self):
        """Test inserting text embeddings only."""
        ids = ["mem1", "mem2"]
        text_embeddings = [[0.1] * 512, [0.2] * 512]
        payloads = [
            {"content": "test 1", "type": "text"},
            {"content": "test 2", "type": "text"},
        ]

        # Should not raise
        self.store.insert_multimodal(
            ids=ids,
            text_embeddings=text_embeddings,
            payloads=payloads,
        )

    def test_insert_vision_only(self):
        """Test inserting vision embeddings only."""
        ids = ["mem1", "mem2"]
        vision_embeddings = [[0.3] * 768, [0.4] * 768]
        payloads = [
            {"content": "image 1", "type": "image"},
            {"content": "image 2", "type": "image"},
        ]

        # Should not raise
        self.store.insert_multimodal(
            ids=ids,
            vision_embeddings=vision_embeddings,
            payloads=payloads,
        )

    def test_insert_both(self):
        """Test inserting both text and vision embeddings."""
        ids = ["mem1"]
        text_embeddings = [[0.1] * 512]
        vision_embeddings = [[0.2] * 768]
        payloads = [{"content": "multimodal", "type": "both"}]

        # Should not raise
        self.store.insert_multimodal(
            ids=ids,
            text_embeddings=text_embeddings,
            vision_embeddings=vision_embeddings,
            payloads=payloads,
        )

    def test_insert_dimension_validation(self):
        """Test that dimension validation works."""
        ids = ["mem1"]

        # Wrong text dimension
        with self.assertRaises(ValueError):
            self.store.insert_multimodal(
                ids=ids,
                text_embeddings=[[0.1] * 100],  # Wrong dimension
            )

        # Wrong vision dimension
        with self.assertRaises(ValueError):
            self.store.insert_multimodal(
                ids=ids,
                vision_embeddings=[[0.1] * 100],  # Wrong dimension
            )

    def test_search_text(self):
        """Test text-only search."""
        # Insert some data
        ids = ["mem1", "mem2", "mem3"]
        text_embeddings = [[0.1] * 512, [0.2] * 512, [0.3] * 512]
        payloads = [
            {"content": f"test {i}", "category": "test"}
            for i in range(3)
        ]

        self.store.insert_multimodal(
            ids=ids,
            text_embeddings=text_embeddings,
            payloads=payloads,
        )

        # Search
        query = [0.15] * 512
        results = self.store.search_text(query_embedding=query, limit=2)

        # Should return results
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 2)

    def test_search_vision(self):
        """Test vision-only search."""
        # Insert some data
        ids = ["mem1", "mem2"]
        vision_embeddings = [[0.1] * 768, [0.2] * 768]
        payloads = [
            {"content": "image 1", "type": "image"},
            {"content": "image 2", "type": "image"},
        ]

        self.store.insert_multimodal(
            ids=ids,
            vision_embeddings=vision_embeddings,
            payloads=payloads,
        )

        # Search
        query = [0.15] * 768
        results = self.store.search_vision(query_embedding=query, limit=2)

        # Should return results
        self.assertGreater(len(results), 0)

    def test_search_hybrid(self):
        """Test hybrid search with RRF fusion."""
        # Insert data with both embeddings
        ids = ["mem1", "mem2", "mem3"]
        text_embeddings = [[0.1] * 512, [0.2] * 512, [0.3] * 512]
        vision_embeddings = [[0.15] * 768, [0.25] * 768, [0.35] * 768]
        payloads = [{"content": f"item {i}"} for i in range(3)]

        self.store.insert_multimodal(
            ids=ids,
            text_embeddings=text_embeddings,
            vision_embeddings=vision_embeddings,
            payloads=payloads,
        )

        # Hybrid search
        query_text = [0.2] * 512
        query_vision = [0.25] * 768
        results = self.store.search_hybrid(
            query_text_embedding=query_text,
            query_vision_embedding=query_vision,
            limit=2,
        )

        # Should return fused results
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 2)

    def test_get_stats(self):
        """Test statistics gathering."""
        # Insert some data
        ids = ["mem1", "mem2"]
        text_embeddings = [[0.1] * 512, [0.2] * 512]
        vision_embeddings = [[0.3] * 768, [0.4] * 768]

        self.store.insert_multimodal(
            ids=ids,
            text_embeddings=text_embeddings,
            vision_embeddings=vision_embeddings,
        )

        # Get stats
        stats = self.store.get_stats()

        self.assertEqual(stats["text_count"], 2)
        self.assertEqual(stats["vision_count"], 2)
        self.assertEqual(stats["total_count"], 2)


class TestHybridVisionRetriever(unittest.TestCase):
    """Test HybridVisionRetriever functionality."""

    def setUp(self):
        """Set up test fixtures."""
        from memscreen.memory.hybrid_retriever import (
            HybridRetrieverConfig,
            HybridVisionRetriever,
        )
        from memscreen.vector_store.multimodal_chroma import MultimodalChromaDB

        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Create mock embedders
        self.mock_text_embedder = Mock()
        self.mock_text_embedder.embed.return_value = [0.1] * 512

        # Mock vision encoder
        self.mock_vision_encoder = Mock()
        self.mock_vision_encoder.encode_image.return_value = [0.2] * 768

        # Create vector store
        self.vector_store = MultimodalChromaDB(
            collection_name="test_retriever",
            path=self.test_dir,
        )

        # Insert test data
        ids = ["mem1", "mem2", "mem3"]
        text_embeddings = [[0.1] * 512, [0.2] * 512, [0.3] * 512]
        vision_embeddings = [[0.15] * 768, [0.25] * 768, [0.35] * 768]
        payloads = [{"content": f"item {i}"} for i in range(3)]

        self.vector_store.insert_multimodal(
            ids=ids,
            text_embeddings=text_embeddings,
            vision_embeddings=vision_embeddings,
            payloads=payloads,
        )

        # Create retriever
        config = HybridRetrieverConfig(
            fusion_weight=0.6,
            enable_caching=True,
        )
        self.retriever = HybridVisionRetriever(
            text_embedder=self.mock_text_embedder,
            vision_encoder=self.mock_vision_encoder,
            vector_store=self.vector_store,
            config=config,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.vector_store.reset()
        shutil.rmtree(self.test_dir)
        self.retriever.clear_cache()

    def test_initialization(self):
        """Test retriever initializes correctly."""
        self.assertIsNotNone(self.retriever.text_embedder)
        self.assertIsNotNone(self.retriever.vision_encoder)
        self.assertIsNotNone(self.retriever.vector_store)
        self.assertEqual(self.retriever.config.fusion_weight, 0.6)

    def test_retrieve_text_only(self):
        """Test text-only retrieval."""
        results = self.retriever.retrieve(query="test query", limit=2)

        # Should return results
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 2)

        # Verify text embedder was called
        self.mock_text_embedder.embed.assert_called_once()

    def test_retrieve_with_filters(self):
        """Test retrieval with metadata filters."""
        results = self.retriever.retrieve(
            query="test query",
            filters={"content": "item 1"},
            limit=10,
        )

        # Should return results
        self.assertIsInstance(results, list)

    def test_query_rewriting(self):
        """Test that query rewriting works."""
        original_query = "red button"
        rewritten = self.retriever._rewrite_query_for_vision(original_query)

        # Should contain visual terms
        self.assertIn("UI element", rewritten)
        self.assertIn("red", rewritten)  # Original term preserved

    def test_cache_functionality(self):
        """Test retrieval caching."""
        # First query
        results1 = self.retriever.retrieve(query="cached query", limit=2)

        # Second query should hit cache
        results2 = self.retriever.retrieve(query="cached query", limit=2)

        # Should be identical
        self.assertEqual(len(results1), len(results2))

        # Check cache stats
        stats = self.retriever.get_cache_stats()
        self.assertEqual(stats["size"], 1)
        self.assertTrue(stats["enabled"])

    def test_clear_cache(self):
        """Test cache clearing."""
        # Add to cache
        self.retriever.retrieve(query="test", limit=2)

        # Clear cache
        self.retriever.clear_cache()

        # Cache should be empty
        stats = self.retriever.get_cache_stats()
        self.assertEqual(stats["size"], 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete hybrid system."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    @unittest.skip("Full integration test - requires models")
    def test_end_to_end_hybrid_search(self):
        """Test complete workflow with real images."""
        from memscreen.embeddings.vision_encoder import VisionEncoder
        from memscreen.embeddings import OllamaEmbedding, BaseEmbedderConfig
        from memscreen.vector_store.multimodal_chroma import MultimodalChromaDB
        from memscreen.memory.hybrid_retriever import HybridVisionRetriever

        # This test would require:
        # 1. Real images
        # 2. sentence-transformers installed
        # 3. Ollama running
        # Skip for CI/CD


if __name__ == "__main__":
    unittest.main()
