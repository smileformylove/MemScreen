### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Vision Encoder for generating visual embeddings using SigLIP or CLIP models.

This module provides a VisionEncoder class that can encode images into visual feature vectors
using state-of-the-art vision-language models like SigLIP or CLIP. These embeddings enable
cross-modal retrieval between text and visual content.
"""

from typing import Optional, List, Dict, Union, Literal
from pathlib import Path
import hashlib
import logging
from datetime import datetime

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

__all__ = [
    "VisionEncoderConfig",
    "VisionEncoder",
]


class VisionEncoderConfig:
    """
    Configuration for VisionEncoder.

    Args:
        model_type: Type of vision model to use ("siglip" or "clip")
        device: Device to run model on ("cpu", "cuda", "mps")
        cache_size: Size of LRU cache for encoded images
        model_name: HuggingFace model name (auto-detected if None)
        embedding_dims: Expected embedding dimensions (auto-detected if None)
    """

    def __init__(
        self,
        model_type: Literal["siglip", "clip"] = "siglip",
        device: str = "cpu",
        cache_size: int = 1000,
        model_name: Optional[str] = None,
        embedding_dims: Optional[int] = None,
    ):
        self.model_type = model_type
        self.device = device
        self.cache_size = cache_size
        self.model_name = model_name
        self.embedding_dims = embedding_dims

        # Auto-detect model defaults
        if self.model_name is None:
            if model_type == "siglip":
                self.model_name = "sentence-transformers/visual_model"
            else:  # clip
                self.model_name = "clip-ViT-B-32-multilingual-v1"

        if self.embedding_dims is None:
            if model_type == "siglip":
                self.embedding_dims = 768
            else:  # clip
                self.embedding_dims = 512


class VisionEncoder:
    """
    Visual feature encoder using SigLIP or CLIP models.

    This encoder converts images into dense vector representations that capture
    visual semantics, enabling cross-modal retrieval and similarity search.

    Supports:
    - SigLIP: 768-dim vectors, better zero-shot performance
    - CLIP: 512-dim vectors, multilingual support (100+ languages)

    Example:
        ```python
        encoder = VisionEncoder(model_type="siglip")
        embedding = encoder.encode_image("screenshot.jpg")
        # Returns: [0.1, -0.2, ..., 0.3]  # 768-dim vector
        ```
    """

    def __init__(self, config: Optional[VisionEncoderConfig] = None):
        """
        Initialize the VisionEncoder.

        Args:
            config: Configuration options. If None, uses defaults.
        """
        if config is None:
            config = VisionEncoderConfig()

        self.config = config
        self.model = None
        self._cache = {}  # Simple LRU cache
        self._cache_order = []  # Track insertion order for LRU

        # Lazy loading - model is loaded on first use
        self._model_loaded = False

        logger.info(
            f"VisionEncoder initialized with {config.model_type} "
            f"({config.model_name}), embedding_dims={config.embedding_dims}"
        )

    def _load_model(self):
        """
        Lazy-load the vision model on first use.

        This reduces startup time and memory usage when vision encoding
        is not immediately needed.
        """
        if self._model_loaded:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading vision model: {self.config.model_name}")
            self.model = SentenceTransformer(
                self.config.model_name,
                device=self.config.device,
            )

            # Verify embedding dimensions
            test_emb = self.model.get_sentence_embedding_dimension()
            if test_emb != self.config.embedding_dims:
                logger.warning(
                    f"Model output dimension ({test_emb}) differs from "
                    f"config ({self.config.embedding_dims}). Using model's dimension."
                )
                self.config.embedding_dims = test_emb

            self._model_loaded = True
            logger.info(f"Vision model loaded successfully (dim={test_emb})")

        except ImportError:
            raise ImportError(
                "sentence-transformers is required for VisionEncoder. "
                "Install it with: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"Failed to load vision model: {e}")
            raise

    def encode_image(
        self,
        image_path: str,
        return_tensor: bool = False,
        use_cache: bool = True,
    ) -> Union[List[float], np.ndarray]:
        """
        Encode an image into a visual embedding vector.

        Args:
            image_path: Path to the image file
            return_tensor: If True, return numpy array; otherwise return list
            use_cache: Whether to use LRU cache for repeated images

        Returns:
            Visual embedding vector (768-dim for SigLIP, 512-dim for CLIP)

        Raises:
            FileNotFoundError: If image file doesn't exist
            Exception: If encoding fails

        Example:
            ```python
            encoder = VisionEncoder()
            embedding = encoder.encode_image("screenshot.png")
            # embedding: [0.123, -0.456, ..., 0.789]  # List[float]
            ```
        """
        # Check cache first
        if use_cache and image_path in self._cache:
            self._update_cache_order(image_path)
            if return_tensor:
                return np.array(self._cache[image_path])
            return self._cache[image_path]

        # Load model on first use
        if not self._model_loaded:
            self._load_model()

        # Verify image exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")

            # Generate embedding
            embedding = self.model.encode(image)

            # Convert to list for JSON serialization
            embedding_list = embedding.tolist()

            # Cache the result
            if use_cache:
                self._add_to_cache(image_path, embedding_list)

            if return_tensor:
                return embedding
            return embedding_list

        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            raise

    def encode_image_batch(
        self,
        image_paths: List[str],
        return_tensor: bool = False,
        use_cache: bool = True,
    ) -> Union[List[List[float]], np.ndarray]:
        """
        Encode multiple images in batch for better performance.

        This is significantly faster than calling encode_image() multiple times
        as it processes all images in one forward pass.

        Args:
            image_paths: List of image file paths
            return_tensor: If True, return numpy array; otherwise return list of lists
            use_cache: Whether to use cache for already-encoded images

        Returns:
            List of embedding vectors, or 2D numpy array if return_tensor=True

        Example:
            ```python
            encoder = VisionEncoder()
            embeddings = encoder.encode_image_batch([
                "screen1.png", "screen2.png", "screen3.png"
            ])
            # embeddings: [[0.1, ...], [0.2, ...], [0.3, ...]]
            ```
        """
        if not self._model_loaded:
            self._load_model()

        # Check which images need encoding
        images_to_encode = []
        indices_to_encode = []
        results = [None] * len(image_paths)

        for i, path in enumerate(image_paths):
            if use_cache and path in self._cache:
                # Use cached version
                self._update_cache_order(path)
                results[i] = self._cache[path]
            else:
                # Mark for encoding
                images_to_encode.append((i, path))

        if not images_to_encode:
            # All cached
            if return_tensor:
                return np.array(results)
            return results

        # Batch encode uncached images
        try:
            # Load images
            images = []
            for idx, path in images_to_encode:
                if not Path(path).exists():
                    logger.warning(f"Image not found, skipping: {path}")
                    continue
                img = Image.open(path).convert("RGB")
                images.append((idx, img))

            # Extract images for batch processing
            idx_list, img_list = zip(*images) if images else ([], [])

            # Batch encode
            embeddings = self.model.encode(list(img_list))

            # Store results and cache
            for idx, embedding in zip(idx_list, embeddings):
                embedding_list = embedding.tolist()
                results[idx] = embedding_list

                # Cache
                original_path = image_paths[idx]
                if use_cache:
                    self._add_to_cache(original_path, embedding_list)

            # Filter out None values (failed encodings)
            final_results = [r for r in results if r is not None]

            if return_tensor:
                return np.array(final_results)
            return final_results

        except Exception as e:
            logger.error(f"Batch encoding failed: {e}")
            # Return whatever we have
            final_results = [r for r in results if r is not None]
            if return_tensor:
                return np.array(final_results)
            return final_results

    def compute_visual_hash(self, image_path: str) -> str:
        """
        Compute a perceptual hash of the image for deduplication.

        Uses pHash (perceptual hash) algorithm which is robust to:
        - Minor image modifications
        - Compression artifacts
        - Slight rotations/scaling

        Args:
            image_path: Path to the image file

        Returns:
            Hexadecimal hash string

        Example:
            ```python
            hash1 = encoder.compute_visual_hash("screen1.png")
            hash2 = encoder.compute_visual_hash("screen2.png")
            if hash1 == hash2:
                print("Images are visually similar")
            ```
        """
        try:
            from PIL import Image
            import imagehash

            image = Image.open(image_path)
            phash = imagehash.phash(image)
            return str(phash)

        except ImportError:
            logger.warning(
                "imagehash not available, falling back to MD5. "
                "Install with: pip install imagehash"
            )
            # Fallback to MD5 hash of file content
            return hashlib.md5(Path(image_path).read_bytes()).hexdigest()

    def extract_visual_features(self, image_path: str) -> Dict[str, any]:
        """
        Extract low-level visual features for fast pre-filtering.

        These features can be used for:
        - Quick similarity filtering before expensive embedding
        - Color-based queries ("red button", "dark theme")
        - Layout analysis

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing:
            - dominant_colors: List of (r, g, b) tuples
            - brightness: Average brightness (0-255)
            - contrast: Standard deviation of pixel values
            - aspect_ratio: Width / height ratio
            - layout_density: Percentage of non-white pixels

        Example:
            ```python
            features = encoder.extract_visual_features("screenshot.png")
            print(f"Brightness: {features['brightness']}")
            print(f"Dominant colors: {features['dominant_colors']}")
            ```
        """
        try:
            image = Image.open(image_path).convert("RGB")
            img_array = np.array(image)

            # Compute brightness (mean pixel value)
            brightness = float(np.mean(img_array))

            # Compute contrast (std of pixel values)
            contrast = float(np.std(img_array))

            # Compute aspect ratio
            width, height = image.size
            aspect_ratio = width / height if height > 0 else 1.0

            # Compute layout density (percentage of non-white pixels)
            if len(img_array.shape) == 3:
                # RGB: count non-white pixels (any channel < 250)
                non_white = np.sum(np.any(img_array < 250, axis=2))
                total_pixels = width * height
            else:
                # Grayscale
                non_white = np.sum(img_array < 250)
                total_pixels = width * height

            layout_density = float(non_white / total_pixels) if total_pixels > 0 else 0.0

            # Extract dominant colors using k-means clustering
            dominant_colors = self._get_dominant_colors(img_array, n_colors=3)

            return {
                "dominant_colors": dominant_colors,
                "brightness": brightness,
                "contrast": contrast,
                "aspect_ratio": aspect_ratio,
                "layout_density": layout_density,
            }

        except Exception as e:
            logger.error(f"Failed to extract features from {image_path}: {e}")
            return {}

    def _get_dominant_colors(self, img_array: np.ndarray, n_colors: int = 3) -> List[tuple]:
        """
        Extract dominant colors from image using k-means clustering.

        Args:
            img_array: RGB image as numpy array
            n_colors: Number of dominant colors to extract

        Returns:
            List of (r, g, b) tuples
        """
        try:
            from sklearn.cluster import KMeans

            # Reshape image to list of pixels
            h, w, c = img_array.shape
            pixels = img_array.reshape(-1, 3).astype(np.float32)

            # Sample pixels for efficiency (max 1000 pixels)
            if len(pixels) > 1000:
                indices = np.random.choice(len(pixels), 1000, replace=False)
                pixels = pixels[indices]

            # Perform k-means clustering
            kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)

            # Get cluster centers (dominant colors)
            colors = kmeans.cluster_centers_.astype(int)
            return [tuple(color) for color in colors]

        except ImportError:
            logger.warning("scikit-learn not available, using average color")
            # Fallback: return average color
            avg_color = tuple(np.mean(img_array, axis=(0, 1)).astype(int))
            return [avg_color] * n_colors

        except Exception as e:
            logger.warning(f"Failed to extract dominant colors: {e}")
            return [(128, 128, 128)] * n_colors

    def _add_to_cache(self, key: str, value: List[float]):
        """Add item to LRU cache."""
        # Remove if already exists
        if key in self._cache:
            self._cache_order.remove(key)

        # Add to cache
        self._cache[key] = value
        self._cache_order.append(key)

        # Enforce cache size limit
        while len(self._cache_order) > self.config.cache_size:
            oldest_key = self._cache_order.pop(0)
            del self._cache[oldest_key]

    def _update_cache_order(self, key: str):
        """Update cache order when item is accessed."""
        if key in self._cache:
            self._cache_order.remove(key)
            self._cache_order.append(key)

    def clear_cache(self):
        """Clear the entire cache."""
        self._cache.clear()
        self._cache_order.clear()
        logger.info("Vision encoder cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dict with 'size' and 'max_size' keys
        """
        return {
            "size": len(self._cache),
            "max_size": self.config.cache_size,
        }


# Convenience function for quick usage
def encode_image(
    image_path: str,
    model_type: Literal["siglip", "clip"] = "siglip",
) -> List[float]:
    """
    Convenience function to encode a single image.

    Args:
        image_path: Path to image file
        model_type: Model type ("siglip" or "clip")

    Returns:
        Embedding vector as list of floats
    """
    config = VisionEncoderConfig(model_type=model_type)
    encoder = VisionEncoder(config)
    return encoder.encode_image(image_path)
