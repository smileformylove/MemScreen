#!/usr/bin/env python3
"""
Prerequisites checker for MemScreen installation.

This script verifies that all required dependencies and configurations
are in place before running MemScreen. It checks:
- Python version
- Ollama installation
- AI model availability
- System permissions
- Hardware requirements
"""

import sys
import platform
import subprocess
import os
from typing import List, Tuple, Optional


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RESET = '\033[0m'


class PrereqChecker:
    """Prerequisites checker for MemScreen."""

    def __init__(self):
        """Initialize the prerequisites checker."""
        self.errors = []
        self.warnings = []
        self.info = []

        # Required models
        self.required_models = [
            "qwen2.5vl:3b",
            "mxbai-embed-large",
        ]

    def print_success(self, message: str):
        """Print a success message."""
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

    def print_error(self, message: str):
        """Print an error message."""
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")

    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

    def print_info(self, message: str):
        """Print an info message."""
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")

    def check_python_version(self) -> Tuple[bool, str]:
        """
        Check Python version >= 3.8.

        Returns:
            Tuple[bool, str]: (is_ok, version_string)
        """
        version = sys.version_info
        current = f"{version.major}.{version.minor}.{version.micro}"
        required = "3.8"

        if version.major > 3:
            return True, current
        elif version.major == 3 and version.minor >= 8:
            return True, current
        else:
            self.errors.append(f"Python {current} installed (need 3.8+)")
            return False, current

    def check_ollama(self) -> bool:
        """
        Check if Ollama is installed.

        Returns:
            bool: True if Ollama is installed
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
                self.print_success(f"Ollama found: {version}")
                return True
            else:
                self.errors.append("Ollama not installed")
                return False
        except FileNotFoundError:
            self.errors.append("Ollama not found in PATH")
            return False
        except subprocess.TimeoutExpired:
            self.errors.append("Ollama command timed out")
            return False
        except Exception as e:
            self.errors.append(f"Error checking Ollama: {e}")
            return False

    def check_ollama_service(self) -> bool:
        """
        Check if Ollama service is running.

        Returns:
            bool: True if Ollama service is running
        """
        try:
            # Try to list models - this only works if service is running
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.print_success("Ollama service is running")
                return True
            else:
                self.warnings.append("Ollama service may not be running")
                return False
        except Exception:
            self.warnings.append("Could not check Ollama service status")
            return False

    def check_models(self) -> List[str]:
        """
        Check which AI models are downloaded.

        Returns:
            List[str]: List of missing model names
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            installed = result.stdout

            missing = []

            for model in self.required_models:
                model_base = model.split(":")[0]
                if model_base in installed:
                    self.print_success(f"Model found: {model}")
                else:
                    self.print_warning(f"Model missing: {model}")
                    missing.append(model)

            return missing
        except Exception as e:
            self.warnings.append(f"Could not check models: {e}")
            return self.required_models

    def check_disk_space(self, required_gb: int = 5) -> bool:
        """
        Check if there's enough disk space.

        Args:
            required_gb: Required disk space in GB

        Returns:
            bool: True if enough space is available
        """
        try:
            if platform.system() == "Windows":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(os.getcwd()), None, None, ctypes.pointer(free_bytes)
                )
                free_gb = free_bytes.value / (1024 ** 3)
            else:
                # Unix-like systems
                stat = os.statvfs(os.getcwd())
                free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)

            if free_gb >= required_gb:
                self.print_success(f"Disk space: {free_gb:.1f}GB free")
                return True
            else:
                self.errors.append(f"Insufficient disk space: {free_gb:.1f}GB free, {required_gb}GB required")
                return False
        except Exception:
            self.warnings.append("Could not check disk space")
            return True  # Don't fail if we can't check

    def check_macos_permissions(self) -> bool:
        """
        Check macOS permissions (screen recording, accessibility).

        Returns:
            bool: True if permissions are granted or not on macOS
        """
        if platform.system() != "Darwin":
            return True

        all_granted = True

        # Check Screen Recording permission
        try:
            result = subprocess.run([
                "defaults", "read", "com.apple.screencapture",
                "record_screen"
            ], capture_output=True, text=True)
            # If command succeeds, permission might be granted
            # This is not definitive - user may need to manually verify
        except:
            self.warnings.append("Screen Recording permission needs verification")
            all_granted = False

        # Check Accessibility permission
        self.warnings.append("Accessibility permission needs manual verification")
        all_granted = False

        if not all_granted:
            self.print_warning("macOS permissions require manual verification")
            self.print_info("  Check System Preferences > Privacy & Security > Privacy")

        return all_granted

    def check_hardware(self) -> bool:
        """
        Check if hardware meets minimum requirements.

        Returns:
            bool: True if hardware is sufficient
        """
        # Check RAM
        try:
            if platform.system() == "Darwin":
                # macOS
                result = subprocess.run(
                    ["sysctl", "hw.memsize"],
                    capture_output=True,
                    text=True
                )
                ram_bytes = int(result.stdout.split()[-1])
                ram_gb = ram_bytes / (1024 ** 3)
            elif platform.system() == "Linux":
                # Linux
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            ram_kb = int(line.split()[1])
                            ram_gb = ram_kb / (1024 ** 2)
                            break
            else:
                # Windows - skip check
                return True

            if ram_gb >= 8:
                self.print_success(f"RAM: {ram_gb:.1f}GB")
                return True
            else:
                self.warnings.append(f"Low RAM: {ram_gb:.1f}GB (8GB+ recommended)")
                return True  # Don't fail, just warn
        except:
            return True  # Don't fail if we can't check

    def check_all(self) -> bool:
        """
        Run all checks and print summary.

        Returns:
            bool: True if all critical checks pass
        """
        print(f"\n{Colors.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
        print(f"{Colors.BLUE}  🔍 MemScreen Prerequisites Checker{Colors.RESET}")
        print(f"{Colors.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")

        print(f"{Colors.BLUE}System Information:{Colors.RESET}")
        print(f"  Platform: {platform.system()} {platform.release()}")
        print(f"  Architecture: {platform.machine()}")
        print()

        # Python version
        print(f"{Colors.BLUE}Checking Python...{Colors.RESET}")
        python_ok, python_ver = self.check_python_version()
        if python_ok:
            self.print_success(f"Python {python_ver}")
        else:
            self.print_error(f"Python {python_ver} (need 3.8+)")
        print()

        # Ollama
        print(f"{Colors.BLUE}Checking Ollama...{Colors.RESET}")
        ollama_ok = self.check_ollama()
        if ollama_ok:
            self.check_ollama_service()
        print()

        # Models
        print(f"{Colors.BLUE}Checking AI Models...{Colors.RESET}")
        missing_models = self.check_models() if ollama_ok else []
        print()

        # Hardware
        print(f"{Colors.BLUE}Checking Hardware...{Colors.RESET}")
        self.check_hardware()
        self.check_disk_space()
        print()

        # macOS permissions
        if platform.system() == "Darwin":
            print(f"{Colors.BLUE}Checking Permissions...{Colors.RESET}")
            self.check_macos_permissions()
            print()

        # Summary
        print(f"{Colors.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
        print(f"{Colors.BLUE}Summary{Colors.RESET}")
        print(f"{Colors.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")

        if python_ok and ollama_ok and not missing_models:
            self.print_success("All critical prerequisites are met!")
            if self.warnings:
                print()
                print(f"{Colors.YELLOW}Warnings:{Colors.RESET}")
                for warning in self.warnings:
                    print(f"  {warning}")
            return True
        else:
            if self.errors:
                print(f"{Colors.RED}Errors found:{Colors.RESET}")
                for error in self.errors:
                    print(f"  {error}")
            if missing_models:
                print(f"\n{Colors.YELLOW}Missing models: {', '.join(missing_models)}{Colors.RESET}")
                print(f"  These can be downloaded during installation")

            return False


def main():
    """Main entry point."""
    checker = PrereqChecker()
    success = checker.check_all()

    print()
    if not success:
        print(f"{Colors.RED}Please fix the errors above before installing MemScreen.{Colors.RESET}")
        sys.exit(1)
    else:
        print(f"{Colors.GREEN}Your system is ready for MemScreen!{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
