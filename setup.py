from setuptools import setup

APP = ["main.py"]

OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName":               "Live Captions",
        "CFBundleDisplayName":        "Live Captions",
        "CFBundleIdentifier":         "com.leaifi.live-captions",
        "CFBundleVersion":            "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "LSMinimumSystemVersion":     "13.0",
        "NSMicrophoneUsageDescription":
            "Live Captions needs microphone access to transcribe speech in real time.",
        "NSSpeechRecognitionUsageDescription":
            "Live Captions uses speech recognition to display real-time captions.",
    },
    "packages": [
        "Speech",
        "AVFoundation",
        "AppKit",
    ],
    "includes": [
        "history",
        "window",
        "recognizer",
    ],
}

setup(
    name="Live Captions",
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
