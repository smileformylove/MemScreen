### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT               ###

"""
Region Configuration Manager for saving and loading custom recording regions.
"""

import json
import os
import time
from typing import Optional, Dict, List, Tuple


class RegionConfig:
    """
    Manage saved region/window configurations.

    Provides persistence for custom regions and tracked windows,
    allowing users to save and reuse recording configurations.
    """

    CONFIG_FILE = "./db/regions.json"

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize RegionConfig manager.

        Args:
            config_file: Path to config file (default: ./db/regions.json)
        """
        self.config_file = config_file or self.CONFIG_FILE
        self.regions = self.load_regions()

    def load_regions(self) -> Dict:
        """
        Load saved regions from file.

        Returns:
            Dictionary of saved regions
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[RegionConfig] Error loading regions: {e}")
                return {}

        return {}

    def save_region(
        self,
        name: str,
        bbox: Tuple[int, int, int, int],
        region_type: str = 'region',
        window_title: Optional[str] = None,
        window_app: Optional[str] = None
    ) -> bool:
        """
        Save a named region or window.

        Args:
            name: Unique name for this region
            bbox: Bounding box as (left, top, right, bottom)
            region_type: Type of region ('region' or 'window')
            window_title: Window title (for 'window' type)
            window_app: Application name (for 'window' type)

        Returns:
            True if saved successfully
        """
        try:
            self.regions[name] = {
                'bbox': list(bbox),  # Convert tuple to list for JSON serialization
                'type': region_type,
                'window_title': window_title,
                'window_app': window_app,
                'created_at': time.time(),
                'last_used': time.time()
            }

            self._save_to_file()
            print(f"[RegionConfig] Saved region: {name}")
            return True

        except Exception as e:
            print(f"[RegionConfig] Error saving region: {e}")
            return False

    def get_region(self, name: str) -> Optional[Dict]:
        """
        Get saved region by name.

        Args:
            name: Region name

        Returns:
            Region dict or None if not found
        """
        region = self.regions.get(name)

        if region:
            # Update last_used timestamp
            region['last_used'] = time.time()
            self._save_to_file()

            # Convert bbox back to tuple
            region['bbox'] = tuple(region['bbox'])
            return region

        return None

    def delete_region(self, name: str) -> bool:
        """
        Delete a saved region.

        Args:
            name: Region name to delete

        Returns:
            True if deleted successfully
        """
        if name in self.regions:
            del self.regions[name]
            self._save_to_file()
            print(f"[RegionConfig] Deleted region: {name}")
            return True

        return False

    def list_regions(self, region_type: Optional[str] = None) -> List[Dict]:
        """
        List all saved regions, optionally filtered by type.

        Args:
            region_type: Filter by type ('region', 'window', or None for all)

        Returns:
            List of region dicts with metadata
        """
        regions = []

        for name, region in self.regions.items():
            if region_type is None or region.get('type') == region_type:
                regions.append({
                    'name': name,
                    'bbox': tuple(region['bbox']),
                    'type': region.get('type', 'region'),
                    'window_title': region.get('window_title'),
                    'window_app': region.get('window_app'),
                    'created_at': region.get('created_at', 0),
                    'last_used': region.get('last_used', 0)
                })

        # Sort by last_used (most recent first)
        regions.sort(key=lambda r: r['last_used'], reverse=True)

        return regions

    def get_recent_regions(self, limit: int = 5) -> List[Dict]:
        """
        Get most recently used regions.

        Args:
            limit: Maximum number of regions to return

        Returns:
            List of recently used region dicts
        """
        regions = self.list_regions()
        return regions[:limit]

    def _save_to_file(self) -> bool:
        """
        Persist regions to file.

        Returns:
            True if saved successfully
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w') as f:
                json.dump(self.regions, f, indent=2)

            return True

        except Exception as e:
            print(f"[RegionConfig] Error saving to file: {e}")
            return False

    def export_to_string(self) -> str:
        """
        Export regions as JSON string.

        Returns:
            JSON string of all regions
        """
        return json.dumps(self.regions, indent=2)

    def import_from_string(self, json_string: str) -> bool:
        """
        Import regions from JSON string.

        Args:
            json_string: JSON string containing regions

        Returns:
            True if imported successfully
        """
        try:
            imported = json.loads(json_string)

            if isinstance(imported, dict):
                self.regions.update(imported)
                self._save_to_file()
                print(f"[RegionConfig] Imported {len(imported)} regions")
                return True

            return False

        except Exception as e:
            print(f"[RegionConfig] Error importing from string: {e}")
            return False
