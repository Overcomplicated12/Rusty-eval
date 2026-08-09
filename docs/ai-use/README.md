# Generative-AI use records

This directory records significant generative-AI assistance used in this project. It implements the Society for Science guidance supplied by the researcher; it is not official legal guidance.

Create a new record before significant AI-assisted methodology, tooling, implementation, debugging, experiment-design, or statistical/tool-selection work:

```bash
python3 scripts/new_ai_log.py --tool Codex --model "unknown" --purpose "Describe the task"
```

Each record preserves the human-authored prompt when available, the disposition of AI output, review, affected artifacts, and disclosure status. Do not reconstruct prompts that were not preserved, and redact secrets before recording them.

The CSV index supports analysis and the Markdown log supports review. They are compliance provenance, not experimental token/performance telemetry.
