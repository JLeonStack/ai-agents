"""VozBar — hold-to-talk dictation bar for macOS (Wispr / Willow loop, local Speech)."""

from __future__ import annotations

import os
import sys
import time

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSFont,
    NSMenu,
    NSMenuItem,
    NSPanel,
    NSPasteboard,
    NSPasteboardTypeString,
    NSScreen,
    NSStatusBar,
    NSTextAlignmentCenter,
    NSTextField,
    NSTimer,
    NSVariableStatusItemLength,
    NSView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
    NSFloatingWindowLevel,
)
from Foundation import NSMakeRect, NSObject
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventGetFlags,
    CGEventGetIntegerValueField,
    CGEventMaskBit,
    CGEventPost,
    CGEventSetFlags,
    CGEventTapCreate,
    CGEventTapEnable,
    CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource,
    CFRunLoopGetCurrent,
    kCFRunLoopCommonModes,
    kCGEventFlagMaskAlternate,
    kCGEventFlagMaskCommand,
    kCGEventFlagsChanged,
    kCGEventTapOptionListenOnly,
    kCGHIDEventTap,
    kCGHeadInsertEventTap,
    kCGKeyboardEventKeycode,
    kCGSessionEventTap,
)
from PyObjCTools import AppHelper

from speech_engine import (
    AUTH_AUTHORIZED,
    SpeechEngine,
    current_status,
    describe_authorization,
)

RIGHT_OPTION = 61
LEFT_OPTION = 58
KEY_V = 9
BAR_WIDTH = 280.0
BAR_HEIGHT = 48.0
MIN_HOLD_SECONDS = 0.28
PASTE_RESTORE_DELAY = 0.40


def main_async(fn, *args):
    AppHelper.callAfter(fn, *args)


class WaveformView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(WaveformView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.mode = "listening"
        self.caption = ""
        self.levels = [0.25, 0.45, 0.7, 0.4, 0.3]
        self.energy = 0.2
        self.click_handler = None
        return self

    def isOpaque(self):
        return False

    def acceptsFirstMouse_(self, _event):
        return True

    def mouseDown_(self, _event):
        if self.click_handler is not None:
            self.click_handler()

    def setMode_caption_(self, mode, caption):
        self.mode = mode
        self.caption = caption or ""
        self.setNeedsDisplay_(True)

    def setEnergy_(self, energy):
        self.energy = max(0.08, min(1.0, float(energy)))
        t = time.time()
        self.levels = [
            max(0.12, min(1.0, self.energy * (0.55 + 0.45 * abs((i * 0.37 + t * 3.1) % 2 - 1))))
            for i in range(5)
        ]
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        pill = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            bounds, bounds.size.height / 2.0, bounds.size.height / 2.0
        )
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.09, 0.09, 0.11, 0.94).setFill()
        pill.fill()

        if self.mode == "listening":
            self.drawBarsInBounds_(bounds)
            return
        self.drawCaptionInBounds_(bounds)

    def drawBarsInBounds_(self, bounds):
        count = len(self.levels)
        gap = 6.0
        bar_w = 5.0
        total = count * bar_w + (count - 1) * gap
        origin_x = (bounds.size.width - total) / 2.0
        mid_y = bounds.size.height / 2.0
        max_h = bounds.size.height * 0.62
        NSColor.colorWithCalibratedWhite_alpha_(0.96, 0.95).setFill()
        for i, level in enumerate(self.levels):
            h = max(6.0, max_h * level)
            x = origin_x + i * (bar_w + gap)
            y = mid_y - h / 2.0
            bar = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(x, y, bar_w, h), 2.5, 2.5
            )
            bar.fill()

    def drawCaptionInBounds_(self, bounds):
        field = NSTextField.alloc().initWithFrame_(
            NSMakeRect(16, 8, bounds.size.width - 32, bounds.size.height - 16)
        )
        field.setBezeled_(False)
        field.setDrawsBackground_(False)
        field.setEditable_(False)
        field.setSelectable_(False)
        field.setAlignment_(NSTextAlignmentCenter)
        field.setFont_(NSFont.systemFontOfSize_(13.0))
        field.setTextColor_(NSColor.colorWithCalibratedWhite_alpha_(0.95, 1.0))
        field.setStringValue_(self.caption)
        field.cell().drawInteriorWithFrame_inView_(field.frame(), self)


class FloatingBar(NSObject):
    def init(self):
        self = objc.super(FloatingBar, self).init()
        if self is None:
            return None
        screen = NSScreen.mainScreen().visibleFrame()
        x = screen.origin.x + (screen.size.width - BAR_WIDTH) / 2.0
        y = screen.origin.y + 28.0
        style = NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, BAR_WIDTH, BAR_HEIGHT),
            style,
            NSBackingStoreBuffered,
            False,
        )
        panel.setLevel_(NSFloatingWindowLevel)
        panel.setOpaque_(False)
        panel.setBackgroundColor_(NSColor.clearColor())
        panel.setHasShadow_(True)
        panel.setMovableByWindowBackground_(True)
        panel.setHidesOnDeactivate_(False)
        panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        view = WaveformView.alloc().initWithFrame_(NSMakeRect(0, 0, BAR_WIDTH, BAR_HEIGHT))
        panel.setContentView_(view)
        panel.setIgnoresMouseEvents_(False)
        self.panel = panel
        self.view = view
        self._hide_timer = None
        return self

    def setClickHandler_(self, handler):
        self.view.click_handler = handler

    def showListening(self):
        self.cancelHide()
        self.view.setMode_caption_("listening", "")
        self.panel.orderFrontRegardless()

    def showTranscribing(self):
        self.cancelHide()
        self.view.setMode_caption_("transcribing", "Transcribiendo…")
        self.panel.orderFrontRegardless()

    def showMessage_hold_(self, message, hold):
        self.cancelHide()
        self.view.setMode_caption_("message", message)
        self.panel.orderFrontRegardless()
        if hold:
            self._hide_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                hold, self, b"hide:", None, False
            )

    def setEnergy_(self, energy):
        if self.view.mode == "listening":
            self.view.setEnergy_(energy)

    def hide_(self, _timer=None):
        self.panel.orderOut_(None)

    def cancelHide(self):
        if self._hide_timer is not None:
            self._hide_timer.invalidate()
            self._hide_timer = None


class PasteInserter(NSObject):
    """Wispr-style insert: stash clipboard, Cmd+V, restore previous clipboard."""

    def init(self):
        self = objc.super(PasteInserter, self).init()
        if self is None:
            return None
        self._previous = None
        self._restore_timer = None
        return self

    def insertText_(self, text: str) -> bool:
        if not text.strip():
            return False
        board = NSPasteboard.generalPasteboard()
        self._previous = board.stringForType_(NSPasteboardTypeString)
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)
        self.postCommandV()
        self._restore_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            PASTE_RESTORE_DELAY, self, b"restoreClipboard:", None, False
        )
        return True

    def restoreClipboard_(self, _timer):
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        if self._previous:
            board.setString_forType_(self._previous, NSPasteboardTypeString)
        self._previous = None

    def postCommandV(self):
        down = CGEventCreateKeyboardEvent(None, KEY_V, True)
        up = CGEventCreateKeyboardEvent(None, KEY_V, False)
        CGEventSetFlags(down, kCGEventFlagMaskCommand)
        CGEventSetFlags(up, kCGEventFlagMaskCommand)
        CGEventPost(kCGHIDEventTap, down)
        CGEventPost(kCGHIDEventTap, up)


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, _notification):
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory
        )
        self.engine = SpeechEngine()
        self.bar = FloatingBar.alloc().init()
        self.bar.setClickHandler_(self.toggleFromBar)
        self.paste = PasteInserter.alloc().init()
        self.holding = False
        self.hold_started = 0.0
        self.hotkey_ok = False
        self.pulseTimer = None
        self.setupStatusItem()
        self.installHotkey()
        self.engine.request_authorization(self.authFinished_)
        print("VozBar listo. Hold Option derecha para dictar.", flush=True)

    def authFinished_(self, status: int):
        def apply():
            self.refreshMenu()
            if int(status) != AUTH_AUTHORIZED:
                self.bar.showMessage_hold_(
                    "Permití Reconocimiento de voz",
                    3.0,
                )

        main_async(apply)

    def setupStatusItem(self):
        item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        item.button().setTitle_("Voz")
        self.status_item = item
        self.refreshMenu()

    def refreshMenu(self):
        menu = NSMenu.alloc().init()
        status = current_status()
        info = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"On-device {status.locale} · {describe_authorization(status.authorization)}",
            None,
            "",
        )
        info.setEnabled_(False)
        menu.addItem_(info)
        hotkey = "Option derecha OK" if self.hotkey_ok else "Atajo: falta Accesibilidad"
        hint = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            hotkey,
            None,
            "",
        )
        hint.setEnabled_(False)
        menu.addItem_(hint)
        menu.addItem_(NSMenuItem.separatorItem())
        talk = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Dictar / parar (si el atajo no anda)",
            b"toggleFromBar",
            "",
        )
        talk.setTarget_(self)
        menu.addItem_(talk)
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Salir",
            b"terminate:",
            "q",
        )
        menu.addItem_(quit_item)
        self.status_item.setMenu_(menu)

    def installHotkey(self):
        def callback(_proxy, event_type, event, _refcon):
            return self.handleFlagsEvent_event_(event_type, event)

        mask = CGEventMaskBit(kCGEventFlagsChanged)
        tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,
            mask,
            callback,
            None,
        )
        self.hotkeyCallback = callback
        if tap is None:
            self.hotkey_ok = False
            self.refreshMenu()
            self.bar.showMessage_hold_(
                "Activá Accesibilidad para el atajo",
                3.5,
            )
            return
        source = CFMachPortCreateRunLoopSource(None, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), source, kCFRunLoopCommonModes)
        CGEventTapEnable(tap, True)
        self.hotkey_ok = True
        self._tap = tap
        self.refreshMenu()

    def handleFlagsEvent_event_(self, event_type, event):
        if event_type != kCGEventFlagsChanged:
            return event
        keycode = int(CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode))
        if keycode not in (RIGHT_OPTION, LEFT_OPTION):
            return event
        # Right Option is the intended Wispr-like key; left Option also works.
        flags = int(CGEventGetFlags(event))
        option_down = bool(flags & kCGEventFlagMaskAlternate)
        if option_down and not self.holding:
            main_async(self.beginHold)
        elif not option_down and self.holding:
            main_async(self.endHold)
        return event

    def toggleFromBar(self):
        if self.holding:
            self.endHold()
        else:
            self.beginHold()

    def beginHold(self):
        if self.holding:
            return
        self.holding = True
        self.hold_started = time.time()
        self.bar.showListening()
        self.pulseTimer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.08, self, b"pulseBars:", None, True
        )

        def on_partial(_text: str):
            pass

        def on_level(level: float):
            main_async(self.bar.setEnergy_, level)

        def on_error(message: str):
            def show():
                self.holding = False
                self.stopPulse()
                self.bar.showMessage_hold_(message, 3.0)

            main_async(show)

        ok = self.engine.start(on_partial=on_partial, on_level=on_level, on_error=on_error)
        if not ok:
            self.holding = False
            self.stopPulse()

    def pulseBars_(self, _timer):
        if not self.holding:
            return
        wave = 0.35 + 0.25 * abs((time.time() * 2.4) % 2 - 1)
        self.bar.setEnergy_(wave)

    def stopPulse(self):
        if self.pulseTimer is not None:
            self.pulseTimer.invalidate()
            self.pulseTimer = None

    def endHold(self):
        if not self.holding:
            return
        self.holding = False
        self.stopPulse()
        elapsed = time.time() - self.hold_started
        if elapsed < MIN_HOLD_SECONDS:
            self.engine.cancel()
            self.bar.hide_(None)
            return
        self.bar.showTranscribing()
        self.engine.stop(on_final=lambda text: main_async(self.finishWithText_, text))

    def finishWithText_(self, text: str):
        cleaned = (text or "").strip()
        if not cleaned:
            self.bar.showMessage_hold_("No escuché nada", 1.6)
            return
        pasted = self.paste.insertText_(cleaned)
        if pasted:
            self.bar.hide_(None)
        else:
            self.bar.showMessage_hold_(cleaned + "  ·  Cmd+V", 2.8)

    def applicationWillTerminate_(self, _notification):
        self.engine.cancel()


def print_check() -> int:
    status = current_status()
    print(f"locale={status.locale}")
    print(f"on_device={status.on_device}")
    print(f"available={status.available}")
    print(f"authorization={describe_authorization(status.authorization)}")
    return 0 if status.on_device and status.available else 1


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in {"--check", "check"}:
        return print_check()
    if os.environ.get("VOZBAR_BUNDLE") != "1":
        print(
            "VozBar necesita el bundle macOS (permisos de micrófono y voz).\n"
            "Corré:  ./run.sh"
        )
        return 2
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
