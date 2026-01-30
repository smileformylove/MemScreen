"""
Folder Batch Processor

This module provides batch processing capabilities for folders,
including recursive scanning, file filtering, and progress tracking.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from threading import Lock

from .file_loader import FileLoader


class FolderProcessor:
    """Batch processor for text files in folders."""

    # Supported text file extensions
    TEXT_EXTENSIONS = {
        '.txt', '.md', '.markdown', '.rst',
        '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp',
        '.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.cfg',
        '.sh', '.bash', '.zsh', '.ps1', '.bat',
        '.csv', '.log', '.conf',
        '.html', '.css', '.scss', '.sass', '.less',
        '.sql', '.r', '.rb', '.go', '.rs', '.swift',
        '.tex', '.bib'
    }

    # Folders to ignore during scanning
    IGNORED_FOLDERS = {
        '__pycache__', '.git', '.svn', 'node_modules',
        'venv', '.venv', 'env', '.env',
        '.idea', '.vscode', 'dist', 'build',
        'target', '.pytest_cache', '.mypy_cache'
    }

    def __init__(self, root_folder: str, callback: Optional[Callable] = None):
        """
        Initialize folder processor.

        Args:
            root_folder: Root folder path (absolute path)
            callback: Progress callback function
                callback(current, total, filename, status)
                status: 'processing', 'success', 'failed', 'skipped'
        """
        self.root_folder = os.path.abspath(root_folder)
        self.callback = callback

        self.results = {
            'success': [],
            'failed': [],
            'skipped': [],
            'total_size': 0
        }

        self._lock = Lock()  # Thread safety

    def scan_directory(self, recursive: bool = True) -> List[str]:
        """
        Scan directory and return all text file paths.

        Args:
            recursive: Whether to recursively scan subdirectories

        Returns:
            List of file paths (absolute paths)
        """
        text_files = []

        try:
            if recursive:
                # Recursive scan
                for root, dirs, files in os.walk(self.root_folder):
                    # Filter out ignored folders
                    dirs[:] = [d for d in dirs if d not in self.IGNORED_FOLDERS]

                    for filename in files:
                        file_path = os.path.join(root, filename)

                        if self.is_text_file(file_path):
                            text_files.append(file_path)
            else:
                # Only scan top-level directory
                for entry in os.scandir(self.root_folder):
                    if entry.is_file() and self.is_text_file(entry.path):
                        text_files.append(entry.path)

        except Exception as e:
            print(f"[FolderProcessor] Scan error: {e}")

        # Sort for consistent processing order
        text_files.sort()

        return text_files

    def is_text_file(self, file_path: str) -> bool:
        """
        Check if file is a text file based on extension.

        Args:
            file_path: File path

        Returns:
            bool: Whether file is a text file
        """
        # Check extension
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.TEXT_EXTENSIONS

    def process_folder(
        self,
        recursive: bool = True,
        max_files: Optional[int] = None,
        max_size_mb: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Batch process all text files in folder.

        Args:
            recursive: Whether to recursively process subdirectories
            max_files: Maximum number of files to process (None = no limit)
            max_size_mb: Maximum total file size limit in MB (None = no limit)

        Returns:
            Dictionary with processing results
        """
        # Scan files
        file_list = self.scan_directory(recursive=recursive)

        # Apply file count limit
        if max_files and len(file_list) > max_files:
            print(f"[FolderProcessor] Limiting to {max_files} files (found {len(file_list)})")
            file_list = file_list[:max_files]

        total = len(file_list)
        print(f"[FolderProcessor] Found {total} text files to process")

        if total == 0:
            return self.results

        # Process files
        for idx, file_path in enumerate(file_list, 1):
            # Progress callback
            if self.callback:
                self.callback(idx, total, file_path, 'processing')

            # Load file
            file_data = self._load_file(file_path)

            if file_data:
                with self._lock:
                    self.results['success'].append(file_data)
                    self.results['total_size'] += file_data['size']

                if self.callback:
                    self.callback(idx, total, file_data['filename'], 'success')
            else:
                with self._lock:
                    self.results['failed'].append(file_path)

                if self.callback:
                    self.callback(idx, total, os.path.basename(file_path), 'failed')

        # Calculate total size in MB
        self.results['total_size_mb'] = self.results['total_size'] / (1024 * 1024)
        self.results['total'] = total
        self.results['success_count'] = len(self.results['success'])
        self.results['failed_count'] = len(self.results['failed'])

        print(f"[FolderProcessor] Processing complete:")
        print(f"  Success: {self.results['success_count']}")
        print(f"  Failed: {self.results['failed_count']}")
        print(f"  Total size: {self.results['total_size_mb']:.2f} MB")

        return self.results

    def _load_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a single file.

        Args:
            file_path: File path (absolute path)

        Returns:
            Dictionary with file info or None:
            {
                'path': str,              # Absolute path
                'relative_path': str,     # Relative path
                'filename': str,          # Filename
                'content': str,           # File content
                'encoding': str,          # Encoding
                'size': int               # Size in bytes
            }
        """
        try:
            # Read file using FileLoader
            content, encoding = FileLoader.read_file(file_path)
            filename = FileLoader.get_filename(file_path)

            # Get relative path
            try:
                relative_path = os.path.relpath(file_path, self.root_folder)
            except ValueError:
                # Windows cross-drive path
                relative_path = file_path

            # Get file size
            size = len(content.encode('utf-8'))

            return {
                'path': file_path,
                'relative_path': relative_path,
                'filename': filename,
                'content': content,
                'encoding': encoding,
                'size': size
            }

        except Exception as e:
            print(f"[FolderProcessor] Failed to load {file_path}: {e}")
            return None

    def get_summary(self) -> str:
        """
        Get processing summary text.

        Returns:
            Summary string
        """
        lines = [
            "Batch Upload Summary",
            "=" * 40,
            f"✓ Successfully loaded: {len(self.results['success'])} files",
            f"✗ Failed: {len(self.results['failed'])} files",
            f"📊 Total size: {self.results.get('total_size_mb', 0):.2f} MB"
        ]

        if self.results['failed']:
            lines.append("\nFailed files:")
            for failed_path in self.results['failed'][:5]:  # Show max 5
                lines.append(f"  - {failed_path}")

            if len(self.results['failed']) > 5:
                lines.append(f"  ... and {len(self.results['failed']) - 5} more")

        return "\n".join(lines)
