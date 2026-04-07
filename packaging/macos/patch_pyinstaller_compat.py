from __future__ import annotations

from pathlib import Path

import PyInstaller.compat


OLD_BLOCK = """        if 'DYLD_LIBRARY_PATH' in os.environ:\n            path = os.environ['DYLD_LIBRARY_PATH']\n            py_prefix += ['-e', 'DYLD_LIBRARY_PATH=%s' % path]\n"""

NEW_BLOCK = """        for env_var in ('DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH', 'PYTHONHOME'):\n            if env_var in os.environ:\n                py_prefix += ['-e', f'{env_var}={os.environ[env_var]}']\n"""


def main() -> None:
    compat_path = Path(PyInstaller.compat.__file__)
    original_text = compat_path.read_text(encoding="utf-8")

    if NEW_BLOCK in original_text:
        print(f"Already patched: {compat_path}")
        return

    if OLD_BLOCK not in original_text:
        raise SystemExit(f"Could not find expected macOS env block in {compat_path}")

    compat_path.write_text(original_text.replace(OLD_BLOCK, NEW_BLOCK), encoding="utf-8")
    print(f"Patched: {compat_path}")


if __name__ == "__main__":
    main()
