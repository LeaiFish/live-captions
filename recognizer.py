import sys
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
        self._sf_recognizer = None

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
            print(f"[Recognizer] Permission denied (status={status}). Grant access in System Settings > Privacy > Speech Recognition.", file=sys.stderr)
            return
        self._sf_recognizer = Speech.SFSpeechRecognizer.alloc().initWithLocale_(
            Speech.NSLocale.alloc().initWithLocaleIdentifier_(self._locale)
        )
        self._begin_engine()
        self._begin_task()

    def _begin_engine(self) -> None:
        self._engine = AVFoundation.AVAudioEngine.alloc().init()
        input_node = self._engine.inputNode()
        fmt = input_node.outputFormatForBus_(0)
        # Capture self so the tap always feeds the current request even after restart_task().
        input_node.installTapOnBus_bufferSize_format_block_(
            0, 1024, fmt,
            lambda buf, _: self._request.appendAudioPCMBuffer_(buf) if self._request else None
        )
        try:
            self._engine.startAndReturnError_(None)
        except Exception as e:
            raise RuntimeError(f"AVAudioEngine failed to start: {e}") from e

    def _begin_task(self) -> None:
        self._request = Speech.SFSpeechAudioBufferRecognitionRequest.alloc().init()
        self._request.setShouldReportPartialResults_(True)
        try:
            self._request.setAddsPunctuation_(True)
        except Exception:
            pass  # macOS <13 fallback

        def handle_result(result, error):
            if error is not None:
                print(f"[Recognizer] Recognition error: {error}", file=sys.stderr)
            if result is None:
                return
            text = result.bestTranscription().formattedString()
            is_final = result.isFinal()
            self._on_result(text, is_final)

        self._task = self._sf_recognizer.recognitionTaskWithRequest_resultHandler_(
            self._request, handle_result
        )

    def restart_task(self) -> None:
        """Cancel current recognition task and start a fresh one on the same audio engine.

        Clears the recognizer's internal accumulated buffer without stopping the
        microphone, so there is no audio gap between sentences.
        """
        if self._task:
            self._task.cancel()
        if self._request:
            self._request.endAudio()
        self._request = None
        self._task = None
        if self._sf_recognizer:
            self._begin_task()

    def stop(self) -> None:
        if self._engine:
            self._engine.stop()
            self._engine.inputNode().removeTapOnBus_(0)
        if self._request:
            self._request.endAudio()
        if self._task:
            self._task.cancel()
        self._request = None
        self._task = None
