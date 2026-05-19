"""Run all tests as a simple sanity script (no pytest required)."""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

modules = [
    "tests.test_huffman",
    "tests.test_lz77",
    "tests.test_text_pipeline",
    "tests.test_manager",
    "tests.test_archive",
]

errors = 0
for mod_name in modules:
    print(f"=== {mod_name} ===")
    mod = importlib.import_module(mod_name)
    for attr in dir(mod):
        if attr.startswith("test_"):
            try:
                getattr(mod, attr)()
                print(f"  {attr}: PASS")
            except Exception as exc:  # noqa
                errors += 1
                print(f"  {attr}: FAIL — {exc}")

if errors:
    print(f"\n{errors} failure(s)")
    sys.exit(1)
print("\nAll tests passed.")
