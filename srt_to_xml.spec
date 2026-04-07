# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs


PROJECT_ROOT = Path(SPECPATH)
ICON_PATH = PROJECT_ROOT / "assets" / "macos" / "srt_to_xml.icns"
MASTER_ICON_PATH = PROJECT_ROOT / "assets" / "macos" / "srt_to_xml.png"
LOCAL_PYTHON_LIB_DIR = PROJECT_ROOT / ".tools" / "python312" / "Python.framework" / "Versions" / "3.12" / "lib"

binaries = collect_dynamic_libs("lxml")
for library_name in ("libssl.3.dylib", "libcrypto.3.dylib"):
    library_path = LOCAL_PYTHON_LIB_DIR / library_name
    if library_path.is_file():
        binaries.append((str(library_path), "."))
datas = [
    (str(ICON_PATH), "assets/macos"),
    (str(MASTER_ICON_PATH), "assets/macos"),
]
hiddenimports = ["PyQt5.sip"]

a = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="srt_to_xml",
    debug=False,
    bootloader_ignore_signals=False,
    exclude_binaries=True,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="srt_to_xml",
)

app = BUNDLE(
    coll,
    name="srt_to_xml.app",
    icon=str(ICON_PATH),
    bundle_identifier="com.ltzz.srt-to-xml",
    version="0.1.0",
    info_plist={
        "CFBundleDisplayName": "srt_to_xml",
        "CFBundleName": "srt_to_xml",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "LSApplicationCategoryType": "public.app-category.productivity",
        "NSHighResolutionCapable": True,
    },
)
