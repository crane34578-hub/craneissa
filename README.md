# Jarvis-like Assistant (OpenAI API)

A practical Python CLI assistant inspired by Jarvis, with safer local command execution and conversation persistence.

## Features
- Conversational assistant using the OpenAI Responses API
- Session memory with configurable history limits
- Optional local command execution via `/run <command>`
- Conversation import/export with `/save` and `/load`
- Better runtime error handling for API/network/rate-limit scenarios

## Requirements
- Python 3.10+
- OpenAI Python SDK

Install dependency:

```bash
pip install -r requirements.txt
```

## Setup
1. Set your API key:

```bash
export OPENAI_API_KEY="your-key-here"
```

2. Run the assistant:

```bash
python jarvis_assistant.py
```

## CLI options

```bash
python jarvis_assistant.py \
  --model gpt-4.1-mini \
  --allow-shell \
  --timeout-seconds 20 \
  --max-history-messages 30
```

- `--allow-shell`: Enables `/run` local command execution
- `--timeout-seconds`: Max execution time for `/run` commands
- `--max-history-messages`: Caps in-memory conversation size
- `--system-prompt`: Overrides the default Jarvis persona

## In-app commands
- `exit` / `quit`: Close assistant
- `/help`: Show command help
- `/history`: Show message count retained in memory
- `/run <command>`: Execute a local command (if `--allow-shell` enabled)
- `/save <file.json>`: Save conversation history
- `/load <file.json>`: Load conversation history

## Notes
- `/run` is disabled by default for safety.
- Commands are parsed without shell expansion (safer than `shell=True`).
