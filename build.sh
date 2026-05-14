#!/bin/bash
set -e

echo "==> Generating icon..."
python generate_icon.py
iconutil -c icns assets/AppIcon.iconset -o assets/AppIcon.icns

echo "==> Building with PyInstaller..."
pyinstaller --noconfirm "Live Captions.spec"

APP="dist/Live Captions.app"

echo "==> Patching Info.plist..."
python3 - << 'PYEOF'
import plistlib

path = "dist/Live Captions.app/Contents/Info.plist"
with open(path, "rb") as f:
    pl = plistlib.load(f)

pl.update({
    "CFBundleShortVersionString": "1.1.0",
    "CFBundleVersion": "1.1.0",
    "CFBundleIconFile": "AppIcon.icns",
    "CFBundleIconName": "AppIcon",
    "LSMinimumSystemVersion": "13.0",
    "LSApplicationCategoryType": "public.app-category.utilities",
    "NSHighResolutionCapable": True,
    "NSPrincipalClass": "NSApplication",
    "NSMicrophoneUsageDescription": "Live Captions needs microphone access to transcribe speech in real time.",
    "NSSpeechRecognitionUsageDescription": "Live Captions uses speech recognition to display real-time captions.",
    "NSHumanReadableCopyright": "© 2026 LeaiFish. MIT License.",
})

with open(path, "wb") as f:
    plistlib.dump(pl, f)

print("  Info.plist patched")
PYEOF

echo "==> Copying AppIcon.icns into Resources..."
cp assets/AppIcon.icns "$APP/Contents/Resources/AppIcon.icns"

echo "==> Done. Built: $APP"
