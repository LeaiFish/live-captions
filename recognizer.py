import threading
from typing import Callable

import AVFoundation
import Speech


class Recognizer:
    """
    Wraps SFSpeechRecognizer + AVAudioEngine to stream mic audio for recognition.
    Calls on_result(text, is_final) from a background thread.
    """

    def __init__(self, on_result: Callable[[str, bool], None], locale: str = "en-US"):
        self._on_result = on_result
        self._locale = locale
        self._engine = None
        self._request = None
        self._task = None

    def start(self) -> None:
        locale = Speech.NSLocale.alloc().initWithLocaleIdentifier_(self._locale)
        recognizer = Speech.SFSpeechRecognizer.alloc().initWithLocale_(locale)

        if not recognizer.isAvailable():
            raise RuntimeError("SFSpeechRecognizer not available on this device.")

        self._request_permission(recognizer)

    def _request_permission(self, recognizer) -> None:
        Speech.SFSpeechRecognizer.requestAuthorization_(self._on_authorized)

    def _on_authorized(self, status) -> None:
        # SFSpeechRecognizerAuthorizationStatusAuthorized == 3
        if status != 3:
            raise RuntimeError(f"Microphone/speech permission denied (status={status}).")
        self._begin(Speech.SFSpeechRecognizer.alloc().initWithLocale_(
            Speech.NSLocale.alloc().initWithLocaleIdentifier_(self._locale)
        ))

    def _begin(self, recognizer) -> None:
        self._engine = AVFoundation.AVAudioEngine.alloc().init()
        input_node = self._engine.inputNode()
        fmt = input_node.outputFormatForBus_(0)

        self._request = Speech.SFSpeechAudioBufferRecognitionRequest.alloc().init()
        self._request.setShouldReportPartialResults_(True)

        def handle_result(result, error):
            if result is None:
                return
            text = result.bestTranscription().formattedString()
            is_final = result.isFinal()
            self._on_result(text, is_final)

        self._task = recognizer.recognitionTaskWithRequest_resultHandler_(
            self._request, handle_result
        )

        input_node.installTapOnBus_bufferSize_format_block_(
            0, 1024, fmt,
            lambda buf, _: self._request.appendAudioPCMBuffer_(buf)
        )

        self._engine.startAndReturnError_(None)

    def stop(self) -> None:
        if self._engine:
            self._engine.stop()
            self._engine.inputNode().removeTapOnBus_(0)
        if self._request:
            self._request.endAudio()
        if self._task:
            self._task.cancel()
