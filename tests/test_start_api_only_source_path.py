import importlib.util
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "setup" / "start_api_only.py"
PROJECT_ROOT = SCRIPT_PATH.parents[1]


def _load_start_api_module():
    spec = importlib.util.spec_from_file_location("start_api_only_module_for_tests", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StartApiOnlySourcePathTest(unittest.TestCase):
    def setUp(self):
        self._original_env_src = os.environ.get("MEMSCREEN_BACKEND_SRC")
        self._original_sys_path = list(sys.path)

    def tearDown(self):
        if self._original_env_src is None:
            os.environ.pop("MEMSCREEN_BACKEND_SRC", None)
        else:
            os.environ["MEMSCREEN_BACKEND_SRC"] = self._original_env_src
        sys.path[:] = self._original_sys_path

    def test_uses_project_root_when_running_from_checkout(self):
        os.environ.pop("MEMSCREEN_BACKEND_SRC", None)
        module = _load_start_api_module()

        injected = module._inject_embedded_source_path()

        self.assertEqual(injected, PROJECT_ROOT)
        self.assertEqual(sys.path[0], str(PROJECT_ROOT))

    def test_env_backend_source_has_priority(self):
        with TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            package_dir = temp_root / "memscreen"
            package_dir.mkdir(parents=True, exist_ok=True)
            (package_dir / "__init__.py").write_text("", encoding="utf-8")
            os.environ["MEMSCREEN_BACKEND_SRC"] = str(temp_root)

            module = _load_start_api_module()
            injected = module._inject_embedded_source_path()

            self.assertEqual(injected, temp_root)
            self.assertEqual(sys.path[0], str(temp_root))


if __name__ == "__main__":
    unittest.main()
