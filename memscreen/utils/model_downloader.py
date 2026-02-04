"""
Model download utility for MemScreen.

Automates downloading and managing AI models required for MemScreen.
Supports checking model status, downloading missing models, and
progress tracking during download.
"""

import subprocess
import sys
import argparse
from typing import List, Tuple, Optional
import time


# Required models for MemScreen
REQUIRED_MODELS = [
    "qwen2.5vl:3b",           # Vision model for screen understanding
    "mxbai-embed-large",      # Text embedding model for semantic search
]

# Optional models for enhanced features
OPTIONAL_MODELS = [
    "llava:7b",               # Alternative vision model
    "nomic-embed-text",       # Alternative embedding model
]


class ModelDownloader:
    """Handles model download and management operations."""

    def __init__(self):
        """Initialize the model downloader."""
        self.required_models = REQUIRED_MODELS
        self.optional_models = OPTIONAL_MODELS

    def check_ollama_installed(self) -> Tuple[bool, str]:
        """
        Check if Ollama is installed and accessible.

        Returns:
            Tuple[bool, str]: (is_installed, version_string)
        """
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, version
            else:
                return False, "Ollama returned error"
        except FileNotFoundError:
            return False, "Ollama not found in PATH"
        except subprocess.TimeoutExpired:
            return False, "Ollama command timed out"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_model(self, model: str) -> bool:
        """
        Check if a model is downloaded.

        Args:
            model: Model name (e.g., "qwen2.5vl:3b")

        Returns:
            bool: True if model is downloaded, False otherwise
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Check if model name appears in output
                # Handle both "qwen2.5vl:3b" and "qwen2.5vl" formats
                model_base = model.split(":")[0]
                return model_base in result.stdout
            return False
        except Exception:
            return False

    def get_model_size(self, model: str) -> Optional[str]:
        """
        Get the size of a downloaded model.

        Args:
            model: Model name

        Returns:
            Optional[str]: Model size string (e.g., "4.2GB") or None if not found
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Parse output to find model size
                for line in result.stdout.split('\n'):
                    if model.split(":")[0] in line:
                        # Format: "MODEL_NAME    SIZE    ID"
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[-2]  # Size is usually second to last
            return None
        except Exception:
            return None

    def download_model(self, model: str, show_progress: bool = True) -> bool:
        """
        Download a single model.

        Args:
            model: Model name to download
            show_progress: Whether to show download progress

        Returns:
            bool: True if download succeeded, False otherwise
        """
        if show_progress:
            print(f"  📥 Downloading {model}...")

        try:
            # Run ollama pull
            process = subprocess.Popen(
                ["ollama", "pull", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            if show_progress:
                # Show progress by reading output
                for line in process.stdout:
                    # Ollama shows progress like "100%|████████████████████|"
                    if "%" in line or "downloading" in line.lower():
                        # Simple progress indicator
                        print(f"    {line.strip()}")
            else:
                # Just wait for completion
                process.wait()

            return_code = process.wait()
            return return_code == 0

        except KeyboardInterrupt:
            print(f"\n  ⚠️  Download of {model} interrupted by user")
            process.kill()
            return False
        except Exception as e:
            if show_progress:
                print(f"  ❌ Error downloading {model}: {str(e)}")
            return False

    def download_models(
        self,
        models: List[str],
        include_optional: bool = False,
        show_progress: bool = True
    ) -> Tuple[int, int]:
        """
        Download multiple models.

        Args:
            models: List of model names to download
            include_optional: Whether to include optional models
            show_progress: Whether to show download progress

        Returns:
            Tuple[int, int]: (successful_count, failed_count)
        """
        if include_optional:
            models = models + self.optional_models

        # Filter out already downloaded models
        missing = [m for m in models if not self.check_model(m)]

        if not missing:
            if show_progress:
                print("✅ All required models are already downloaded")
            return 0, 0

        if show_progress:
            print(f"🧠 Downloading {len(missing)} model(s)...")

        successful = 0
        failed = 0

        for model in missing:
            if self.download_model(model, show_progress):
                successful += 1
                if show_progress:
                    print(f"  ✅ {model} downloaded successfully")
            else:
                failed += 1
                if show_progress:
                    print(f"  ❌ Failed to download {model}")

        return successful, failed

    def list_installed_models(self) -> List[str]:
        """
        List all installed models.

        Returns:
            List[str]: List of installed model names
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                models = []
                for line in result.stdout.split('\n')[1:]:  # Skip header
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            return []
        except Exception:
            return []

    def get_status(self) -> dict:
        """
        Get comprehensive status of models.

        Returns:
            dict: Status information including installed/missing models
        """
        installed_models = self.list_installed_models()

        required_status = {}
        for model in self.required_models:
            model_base = model.split(":")[0]
            is_installed = any(model_base in m for m in installed_models)
            required_status[model] = {
                "installed": is_installed,
                "size": self.get_model_size(model) if is_installed else None
            }

        return {
            "ollama_installed": self.check_ollama_installed()[0],
            "required_models": required_status,
            "total_installed": len(installed_models),
        }


def main():
    """Command-line interface for model downloading."""
    parser = argparse.ArgumentParser(
        description="Download and manage MemScreen AI models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                    List installed models
  %(prog)s --download                Download all required models
  %(prog)s --download --optional     Download all models including optional
  %(prog)s --status                  Show model installation status
        """
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all installed models"
    )

    parser.add_argument(
        "--download",
        action="store_true",
        help="Download missing required models"
    )

    parser.add_argument(
        "--optional",
        action="store_true",
        help="Include optional models in download"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show detailed status of model installation"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if Ollama is installed"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    downloader = ModelDownloader()
    show_progress = not args.quiet

    # Check Ollama installation
    ollama_ok, ollama_version = downloader.check_ollama_installed()
    if not ollama_ok:
        print("❌ Ollama is not installed or not in PATH")
        print("   Please install Ollama from https://ollama.com/")
        sys.exit(1)

    if args.check:
        print(f"✅ Ollama is installed: {ollama_version}")
        sys.exit(0)

    if args.list:
        print("📋 Installed models:")
        models = downloader.list_installed_models()
        if models:
            for model in models:
                size = downloader.get_model_size(model)
                size_str = f" ({size})" if size else ""
                print(f"  - {model}{size_str}")
        else:
            print("  No models installed")
        sys.exit(0)

    if args.status:
        status = downloader.get_status()
        print("📊 MemScreen Model Status")
        print("-" * 50)
        print(f"Ollama: ✅ Installed ({ollama_version})")
        print(f"Total models installed: {status['total_installed']}")
        print("\nRequired models:")
        for model, info in status['required_models'].items():
            status_str = "✅" if info['installed'] else "❌"
            size_str = f" ({info['size']})" if info['size'] else ""
            print(f"  {status_str} {model}{size_str}")
        sys.exit(0)

    if args.download:
        successful, failed = downloader.download_models(
            downloader.required_models,
            include_optional=args.optional,
            show_progress=show_progress
        )

        if show_progress:
            print("-" * 50)
            if failed == 0:
                print(f"✅ Successfully downloaded {successful} model(s)")
            else:
                print(f"⚠️  Downloaded {successful} model(s), {failed} failed")

        sys.exit(0 if failed == 0 else 1)

    # If no arguments, run interactive mode
    if len(sys.argv) == 1:
        status = downloader.get_status()
        print("🦉 MemScreen Model Manager")
        print("-" * 50)

        missing_required = [
            m for m, info in status['required_models'].items()
            if not info['installed']
        ]

        if missing_required:
            print(f"⚠️  Missing {len(missing_required)} required model(s):")
            for model in missing_required:
                print(f"  - {model}")
            print()

            response = input("Download missing models? (y/n): ").strip().lower()
            if response == 'y':
                successful, failed = downloader.download_models(
                    downloader.required_models,
                    show_progress=True
                )
                if failed == 0:
                    print("\n✅ All models downloaded successfully!")
                else:
                    print(f"\n⚠️  {failed} model(s) failed to download")
        else:
            print("✅ All required models are installed")
            print(f"   Total: {status['total_installed']} models")

        sys.exit(0)


if __name__ == "__main__":
    main()
