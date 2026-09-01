# AI Agents

Two practical agent-building projects developed for an AI agents workshop:

- **[VozBar](vozbar/)** — a small, local, hold-to-talk dictation bar for macOS.
- **[Weekly Repository Summary Contract](contrato-resumen-semanal-repo/)** — a structured prompt contract for turning a repository's `git log` into a weekly status report.

## Repository structure

```text
.
├── contrato-resumen-semanal-repo/
│   ├── system_prompt.md
│   ├── user_prompt.md
│   ├── runs/
│   └── README.md
└── vozbar/
    ├── app.py
    ├── speech_engine.py
    ├── requirements.txt
    ├── run.sh
    └── README.md
```

## Projects

### VozBar

VozBar uses Apple's on-device Speech framework through PyObjC. Hold the right Option key to dictate; releasing it transcribes the speech and pastes the result into the focused application. It requires macOS and permissions for the microphone, speech recognition, and accessibility.

To run it on a compatible Mac:

```bash
cd vozbar
./run.sh
```

See [`vozbar/README.md`](vozbar/README.md) for behavior, requirements, known limitations, and implementation notes.

### Weekly repository summary contract

This project contains a system prompt and a user prompt for an agent that converts raw Git history into predictable JSON. The contract defines the agent's role, context, task, restrictions, output schema, and examples. The `runs/` directory documents three real executions and the iterations made to improve the contract.

See [`contrato-resumen-semanal-repo/README.md`](contrato-resumen-semanal-repo/README.md) for the full background and results.

## Requirements

- macOS and Python with PyObjC for VozBar.
- An agent or LLM capable of following the prompt contract for the weekly summary project.

## License

No license has been specified for this repository yet.
