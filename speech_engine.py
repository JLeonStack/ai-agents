"""On-device speech recognition via Apple's Speech framework.

No cloud API. If the locale cannot run on-device, start() fails instead of
silently sending audio to Apple's servers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from AVFoundation import AVAudioEngine
from Foundation import NSLocale
from Speech import (
    SFSpeechAudioBufferRecognitionRequest,
    SFSpeechRecognizer,
    SFSpeechRecognizerAuthorizationStatusAuthorized,
    SFSpeechRecognizerAuthorizationStatusDenied,
    SFSpeechRecognizerAuthorizationStatusRestricted,
)


LOCALE_CANDIDATES = ("es-AR", "es-ES", "es-MX", "en-US")

AUTH_DENIED = int(SFSpeechRecognizerAuthorizationStatusDenied)
AUTH_RESTRICTED = int(SFSpeechRecognizerAuthorizationStatusRestricted)
AUTH_AUTHORIZED = int(SFSpeechRecognizerAuthorizationStatusAuthorized)


@dataclass(frozen=True)
class EngineStatus:
    locale: str
    on_device: bool
    available: bool
    authorization: int


def describe_authorization(status: int) -> str:
    if status == AUTH_AUTHORIZED:
        return "authorized"
    if status == AUTH_DENIED:
        return "denied"
    if status == AUTH_RESTRICTED:
        return "restricted"
    return "notDetermined"


def pick_on_device_recognizer() -> tuple[object | None, str | None]:
    for ident in LOCALE_CANDIDATES:
        locale = NSLocale.localeWithLocaleIdentifier_(ident)
        recognizer = SFSpeechRecognizer.alloc().initWithLocale_(locale)
        if recognizer is None:
            continue
        if bool(recognizer.supportsOnDeviceRecognition()) and bool(
            recognizer.isAvailable()
        ):
            actual = str(recognizer.locale().localeIdentifier())
            return recognizer, actual
    return None, None


def current_status() -> EngineStatus:
    recognizer, locale = pick_on_device_recognizer()
    auth = int(SFSpeechRecognizer.authorizationStatus())
    if recognizer is None:
        return EngineStatus(
            locale="none",
            on_device=False,
            available=False,
            authorization=auth,
        )
    return EngineStatus(
        locale=locale or "unknown",
        on_device=True,
        available=bool(recognizer.isAvailable()),
        authorization=auth,
    )


class SpeechEngine:
    """Hold-to-talk session: start on key-down, stop on key-up."""

    def __init__(self) -> None:
        self._recognizer, self.locale_id = pick_on_device_recognizer()
        self._engine = None
        self._request = None
        self._task = None
        self._input_node = None
        self._partial = ""
        self._final = ""
        self._on_partial: Callable[[str], None] | None = None
        self._on_level: Callable[[float], None] | None = None
        self._on_error: Callable[[str], None] | None = None
        self._on_final: Callable[[str], None] | None = None
        self._running = False

    def request_authorization(self, done: Callable[[int], None]) -> None:
        def handler(status: int) -> None:
            done(int(status))

        SFSpeechRecognizer.requestAuthorization_(handler)

    def can_run_on_device(self) -> bool:
        return self._recognizer is not None and bool(
            self._recognizer.supportsOnDeviceRecognition()
        )

    def start(
        self,
        on_partial: Callable[[str], None] | None = None,
        on_level: Callable[[float], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> bool:
        if self._running:
            return True
        if self._recognizer is None or not self.can_run_on_device():
            if on_error:
                on_error("No hay reconocimiento on-device para este Mac/idioma.")
            return False
        if int(SFSpeechRecognizer.authorizationStatus()) != AUTH_AUTHORIZED:
            if on_error:
                on_error("Falta permiso de Reconocimiento de voz.")
            return False

        self._on_partial = on_partial
        self._on_level = on_level
        self._on_error = on_error
        self._on_final = None
        self._partial = ""
        self._final = ""

        request = SFSpeechAudioBufferRecognitionRequest.alloc().init()
        request.setShouldReportPartialResults_(True)
        request.setRequiresOnDeviceRecognition_(True)
        self._request = request

        engine = AVAudioEngine.alloc().init()
        input_node = engine.inputNode()
        fmt = input_node.outputFormatForBus_(0)
        if fmt is None or fmt.sampleRate() == 0:
            if on_error:
                on_error("No se pudo abrir el micrófono.")
            return False

        def tap(buffer, _when) -> None:
            if self._request is None:
                return
            self._request.appendAudioPCMBuffer_(buffer)
            if self._on_level:
                self._on_level(_buffer_level(buffer))

        try:
            input_node.removeTapOnBus_(0)
        except Exception:
            pass
        input_node.installTapOnBus_bufferSize_format_block_(0, 1024, fmt, tap)

        engine.prepare()
        started = engine.startAndReturnError_(None)
        if isinstance(started, tuple):
            started = started[0]
        if not started:
            if on_error:
                on_error("AVAudioEngine no arrancó. Revisá el permiso de Micrófono.")
            return False

        self._engine = engine
        self._input_node = input_node
        self._running = True

        def result_handler(result, err) -> None:
            if err is not None and self._on_error and self._running:
                self._on_error(str(err))
            if result is None:
                if self._on_final and not self._running:
                    self._on_final(self._final or self._partial)
                    self._on_final = None
                return
            text = str(result.bestTranscription().formattedString())
            if result.isFinal():
                self._final = text
                if self._on_final:
                    self._on_final(text)
                    self._on_final = None
            else:
                self._partial = text
                if self._on_partial:
                    self._on_partial(text)

        self._task = self._recognizer.recognitionTaskWithRequest_resultHandler_(
            request, result_handler
        )
        return True

    def stop(self, on_final: Callable[[str], None] | None = None) -> None:
        self._on_final = on_final
        self._running = False
        if self._request is not None:
            self._request.endAudio()
        self._teardown_audio()
        if on_final and self._task is None:
            on_final(self._final or self._partial)

    def cancel(self) -> None:
        self._on_final = None
        self._running = False
        if self._task is not None:
            self._task.cancel()
        self._teardown_audio()
        self._request = None
        self._task = None

    def _teardown_audio(self) -> None:
        if self._engine is not None:
            self._engine.stop()
        if self._input_node is not None:
            try:
                self._input_node.removeTapOnBus_(0)
            except Exception:
                pass
        self._engine = None
        self._input_node = None


def _buffer_level(buffer) -> float:
    """Cheap 0..1 meter. If PyObjC won't give float samples, pulse instead."""
    try:
        n = int(buffer.frameLength())
        if n <= 0:
            return 0.08
        data = buffer.floatChannelData()
        if data is None:
            return 0.22
        channel = data[0]
        step = max(n // 64, 1)
        total = 0.0
        count = 0
        for i in range(0, n, step):
            sample = float(channel[i])
            total += sample * sample
            count += 1
        if count == 0:
            return 0.08
        rms = (total / count) ** 0.5
        return max(0.08, min(1.0, rms * 8.0))
    except Exception:
        return 0.22
