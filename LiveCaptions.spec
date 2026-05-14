# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['Speech', 'AVFoundation', 'AppKit', 'history', 'window', 'recognizer'],
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
    exclude_binaries=True,
    name='Live Captions',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='Live Captions',
)

app = BUNDLE(
    coll,
    name='Live Captions.app',
    icon='assets/AppIcon.icns',
    bundle_identifier='com.leaifi.live-captions',
    version='1.1.0',
    info_plist={
        'CFBundleName':               'Live Captions',
        'CFBundleDisplayName':        'Live Captions',
        'CFBundleShortVersionString': '1.1.0',
        'CFBundleIconName':           'AppIcon',
        'LSMinimumSystemVersion':     '13.0',
        'LSApplicationCategoryType':  'public.app-category.utilities',
        'NSHighResolutionCapable':    True,
        'NSPrincipalClass':           'NSApplication',
        'NSMicrophoneUsageDescription':
            'Live Captions needs microphone access to transcribe speech in real time.',
        'NSSpeechRecognitionUsageDescription':
            'Live Captions uses speech recognition to display real-time captions.',
        'NSHumanReadableCopyright':   '© 2026 LeaiFish. MIT License.',
    },
)
