### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Temporal visual memory for video sequence analysis.

This module provides functionality to:
- Detect scene changes in video sequences
- Identify event boundaries
- Generate event summaries
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

__all__ = [
    "TemporalVisionMemory",
    "TemporalMemoryConfig",
]


class TemporalMemoryConfig:
    """
    Configuration for temporal vision memory.

    Args:
        scene_change_threshold: Threshold for detecting scene changes
        min_event_duration: Minimum duration for an event (seconds)
        max_gap_duration: Maximum gap between frames for same event (seconds)
    """

    def __init__(
        self,
        scene_change_threshold: float = 0.3,
        min_event_duration: float = 1.0,
        max_gap_duration: float = 2.0,
    ):
        self.scene_change_threshold = scene_change_threshold
        self.min_event_duration = min_event_duration
        self.max_gap_duration = max_gap_duration


class TemporalVisionMemory:
    """
    Temporal visual memory for video sequence analysis.

    Detects events and scene changes in video sequences using
    visual embeddings to compute frame-to-frame distances.

    Example:
        ```python
        memory = TemporalVisionMemory(
            vision_encoder=encoder,
            llm=llm
        )

        events = memory.process_video_segment(
            video_path="recording.mp4",
            frames=[frame1, frame2, ...],
            timestamps=[t1, t2, ...]
        )

        for event in events:
            print(f"Event: {event['summary']}")
            print(f"Duration: {event['end_time']} - {event['start_time']}")
        ```
    """

    def __init__(
        self,
        vision_encoder,
        llm,
        config: Optional[TemporalMemoryConfig] = None,
    ):
        """
        Initialize temporal vision memory.

        Args:
            vision_encoder: Vision encoder for frame embeddings
            llm: LLM for event summarization
            config: Configuration options
        """
        if config is None:
            config = TemporalMemoryConfig()

        self.vision_encoder = vision_encoder
        self.llm = llm
        self.config = config

        logger.info(
            f"TemporalVisionMemory initialized "
            f"(change_threshold={config.scene_change_threshold})"
        )

    def process_video_segment(
        self,
        video_path: str,
        frames: List[np.ndarray],
        timestamps: List[datetime],
    ) -> List[Dict]:
        """
        Process video segment and detect events.

        Args:
            video_path: Path to video file
            frames: List of video frames as numpy arrays
            timestamps: List of timestamps for each frame

        Returns:
            List of detected events with:
            - start_frame: int
            - end_frame: int
            - start_time: str
            - end_time: str
            - summary: str
            - embedding: List[float]
        """
        if len(frames) != len(timestamps):
            raise ValueError("Frames and timestamps must have same length")

        if len(frames) < 2:
            logger.warning("Not enough frames for event detection")
            return []

        logger.info(f"Processing {len(frames)} frames from {video_path}")

        # Step 1: Extract features from each frame
        frame_features = self._extract_frame_features(frames, video_path)

        # Step 2: Detect scene changes (event boundaries)
        events = self._detect_scene_changes(
            frame_features, timestamps, video_path
        )

        # Step 3: Generate summaries for each event
        for event in events:
            event_frames = frames[event['start_frame']:event['end_frame']]
            event['summary'] = self._summarize_event(event_frames)
            event['video_path'] = video_path

        logger.info(f"Detected {len(events)} events in {video_path}")

        return events

    def _extract_frame_features(
        self,
        frames: List[np.ndarray],
        video_path: str,
    ) -> List[Dict]:
        """
        Extract features from video frames.

        Args:
            frames: List of frames
            video_path: Video file path

        Returns:
            List of feature dicts per frame
        """
        features = []

        # For efficiency, we'd save frames to disk and batch encode
        # For now, placeholder implementation
        for i, frame in enumerate(frames):
            # TODO: Save frame to temp file, encode with vision_encoder
            # For now, use simple features

            feature = {
                'frame_index': i,
                'brightness': float(np.mean(frame)),
                'contrast': float(np.std(frame)),
                # 'embedding': vision_encoding,  # TODO
                'embedding': None,  # Placeholder
            }
            features.append(feature)

        logger.debug(f"Extracted features from {len(frames)} frames")
        return features

    def _detect_scene_changes(
        self,
        frame_features: List[Dict],
        timestamps: List[datetime],
        video_path: str,
    ) -> List[Dict]:
        """
        Detect scene changes based on frame distances.

        Args:
            frame_features: List of frame features
            timestamps: Frame timestamps
            video_path: Video path

        Returns:
            List of events
        """
        events = []

        if len(frame_features) < 2:
            return events

        # Compute distances between consecutive frames
        distances = []
        for i in range(1, len(frame_features)):
            dist = self._compute_frame_distance(
                frame_features[i-1],
                frame_features[i]
            )
            distances.append(dist)

        if not distances:
            return events

        # Detect peaks (scene changes)
        threshold = np.mean(distances) + self.config.scene_change_threshold * np.std(distances)
        change_points = [
            i for i, d in enumerate(distances)
            if d > threshold
        ]

        # Build events from change points
        start = 0
        for change_point in change_points:
            if change_point - start > 0:  # Ensure non-empty event
                events.append({
                    'start_frame': start,
                    'end_frame': change_point,
                    'start_time': timestamps[start].isoformat(),
                    'end_time': timestamps[change_point].isoformat(),
                })
            start = change_point

        # Last event
        if start < len(frame_features):
            events.append({
                'start_frame': start,
                'end_frame': len(frame_features),
                'start_time': timestamps[start].isoformat(),
                'end_time': timestamps[-1].isoformat(),
            })

        logger.info(
            f"Detected {len(events)} events from {len(change_points)} scene changes"
        )

        return events

    def _compute_frame_distance(
        self,
        frame1: Dict,
        frame2: Dict,
    ) -> float:
        """
        Compute distance between two frames.

        Args:
            frame1: First frame features
            frame2: Second frame features

        Returns:
            Distance score (higher = more different)
        """
        # If we have embeddings, use cosine distance
        if frame1.get('embedding') and frame2.get('embedding'):
            emb1 = np.array(frame1['embedding'])
            emb2 = np.array(frame2['embedding'])
            return float(1.0 - np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))

        # Otherwise, use simple feature distance
        # Combine brightness and contrast differences
        brightness_diff = abs(frame1['brightness'] - frame2['brightness'])
        contrast_diff = abs(frame1['contrast'] - frame2['contrast'])

        # Normalize (brightness is 0-255, contrast is typically 0-100)
        brightness_diff = brightness_diff / 255.0
        contrast_diff = contrast_diff / 100.0

        return float(brightness_diff + contrast_diff)

    def _summarize_event(self, event_frames: List[np.ndarray]) -> str:
        """
        Generate summary for an event.

        Args:
            event_frames: Frames in the event

        Returns:
            Event summary string
        """
        try:
            # Sample key frames (start, middle, end)
            num_frames = len(event_frames)
            if num_frames == 0:
                return "Empty event"

            # For now, return basic summary
            # In production, use vision model to describe frames

            summary = f"Event with {num_frames} frames"

            return summary

        except Exception as e:
            logger.error(f"Failed to summarize event: {e}")
            return f"Event ({len(event_frames)} frames)"

    def store_temporal_memory(
        self,
        events: List[Dict],
        vector_store,
        video_id: str,
    ):
        """
        Store temporal events in vector store.

        Args:
            events: List of events from process_video_segment()
            vector_store: Vector store
            video_id: Video ID
        """
        for i, event in enumerate(events):
            event_id = f"{video_id}_event_{i}"

            payload = {
                'event_type': 'video_segment',
                'start_frame': event['start_frame'],
                'end_frame': event['end_frame'],
                'start_time': event['start_time'],
                'end_time': event['end_time'],
                'summary': event.get('summary', ''),
                'video_path': event.get('video_path', ''),
                'video_id': video_id,
            }

            # Store with embedding if available
            embedding = event.get('embedding')

            vector_store.insert_multimodal(
                ids=[event_id],
                text_embeddings=[embedding] if embedding else None,
                payloads=[payload],
            )

        logger.info(f"Stored {len(events)} temporal events for {video_id[:8]}")
