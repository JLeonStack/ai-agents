# Local E2E smoke checks

Scope marker: E2E_PIPELINE_OK

A disposable Linux VM run of the real-LLM factory pipeline checks this
repo. The checks are deliberately narrow and confirm only that committed
sources parse — they do not run or exercise the apps.

## What the Linux VM checks

- Python syntax of `vozbar/app.py` and `vozbar/speech_engine.py`
  (`python3 -m py_compile vozbar/app.py vozbar/speech_engine.py`)
- JSON parsing of `contrato-resumen-semanal-repo/runs/*.json` — today
  `run2_output.json` and `run3_output.json`; `run1_output.txt` is plain
  text and is not covered by the glob.

## What is not tested on Linux

VozBar is a macOS menu-bar app built on PyObjC, so none of this runs here:

- macOS speech recognition (`SFSpeechRecognizer`, `vozbar/speech_engine.py`)
- the menu-bar UI (`NSStatusBar`, `vozbar/app.py`)
- hotkeys / hold-to-talk (Quartz `CGEventTap`, `vozbar/app.py`)
- microphone and speech-recognition permissions (`vozbar/macos/Info.plist`)
- the PyObjC runtime: `import objc` fails on Linux, so these modules are
  syntax-checked but never imported or run here.

A green Linux smoke check means "the sources parse", not "VozBar works";
macOS behavior must still be checked by hand on a Mac.
