"""
PyInstaller runtime hook to disable ChromaDB telemetry.

This hook prevents ChromaDB from importing telemetry modules
that cause import errors in the bundled application.

Run before any other imports to intercept ChromaDB's telemetry system.
"""

import sys
from types import ModuleType


class FakeTelemetryClass:
    """Fake telemetry class that does nothing."""
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        """Return a no-op class or method for any attribute access."""
        return FakeTelemetryClass()

    def __iter__(self):
        """Return an empty iterator."""
        return iter([])


class FakeTelemetryModule(ModuleType):
    """
    Fake telemetry module to prevent ChromaDB from importing
    the problematic chromadb.telemetry.* modules.

    This module behaves like a real Python module and can handle
    iteration and attribute access without breaking ChromaDB.
    """

    def __init__(self, name):
        super().__init__(name)
        self.__file__ = '<fake telemetry module>'
        self.__path__ = []

    def __getattr__(self, name):
        """Return a fake class/function for any attribute access."""
        return FakeTelemetryClass()

    def __iter__(self):
        """Return an empty iterator."""
        return iter([])

    def __dir__(self):
        """Return empty directory to prevent introspection."""
        return []


class ChromaDBTelemetryFinder:
    """
    Meta path importer that intercepts all chromadb.telemetry.* imports
    and returns fake modules to prevent import errors.
    """

    def find_spec(self, fullname, path, target=None):
        """Intercept chromadb.telemetry.* imports."""
        if fullname.startswith('chromadb.telemetry'):
            # Create and return a fake module immediately
            if fullname not in sys.modules:
                fake_module = FakeTelemetryModule(fullname)
                sys.modules[fullname] = fake_module
            # Return None to signal that the module is already in sys.modules
            return None
        return None


# Install fake telemetry modules for common ChromaDB telemetry paths
fake_telemetry = FakeTelemetryModule('chromadb.telemetry')
sys.modules['chromadb.telemetry'] = fake_telemetry

# Pre-register common telemetry submodules
for module_name in [
    'chromadb.telemetry.product',
    'chromadb.telemetry.product.posthog',
    'chromadb.telemetry.product.events',
    'chromadb.telemetry.product.segment',
    'chromadb.telemetry.opentelemetry',
]:
    fake_module = FakeTelemetryModule(module_name)
    sys.modules[module_name] = fake_module

# Install meta path hook to catch any other chromadb.telemetry.* imports
telemetry_finder = ChromaDBTelemetryFinder()
sys.meta_path.insert(0, telemetry_finder)
