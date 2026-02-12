#!/usr/bin/env python3
"""Jarvis-like assistant CLI using the OpenAI Responses API.

Highlights:
- Conversational loop with memory
- Optional local command execution (disabled by default)
- Conversation export/import helpers
- Better error handling and safer subprocess execution
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SYSTEM_PROMPT = (
    "You are Jarvis, a concise and helpful AI technical assistant. "
    "Be clear, action-oriented, and professional. "
    "If a user asks for risky commands, explain the risks briefly first."
)


@dataclass
class AssistantConfig:
    model: str
    allow_shell: bool
    timeout_seconds: int
    max_history_messages: int
    system_prompt: str


class JarvisAssistant:
    def __init__(self, config: AssistantConfig) -> None:
        from openai import APIConnectionError, APIError, OpenAI, RateLimitError

        self.config = config
        self.client = OpenAI()
        self.api_connection_error = APIConnectionError
        self.api_error = APIError
        self.rate_limit_error = RateLimitError
        self.history: list[dict[str, str]] = [
            {"role": "system", "content": self.config.system_prompt}
        ]

    def ask(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        self._trim_history()

        try:
            response = self.client.responses.create(
                model=self.config.model,
                input=self.history,
                temperature=0.6,
            )
        except self.rate_limit_error:
            return "I hit rate limits. Please wait a moment and try again."
        except self.api_connection_error:
            return "I could not connect to OpenAI. Check your network and try again."
        except self.api_error as exc:
            return f"OpenAI API error: {exc}"

        output_text = (response.output_text or "").strip()
        if not output_text:
            output_text = "I did not receive a text response. Please try rephrasing."

        self.history.append({"role": "assistant", "content": output_text})
        self._trim_history()
        return output_text

    def execute_shell(self, command: str) -> str:
        if not self.config.allow_shell:
            return "Shell execution is disabled. Re-run with --allow-shell to enable it."

        try:
            parts = shlex.split(command)
        except ValueError as exc:
            return f"Invalid command syntax: {exc}"

        if not parts:
            return "No command provided."

        try:
            result = subprocess.run(
                parts,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )
        except FileNotFoundError:
            return f"Command not found: {parts[0]}"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {self.config.timeout_seconds}s"
        except OSError as exc:
            return f"Command execution failed: {exc}"

        output: list[str] = [f"$ {' '.join(parts)}"]
        if result.stdout:
            output.append(result.stdout.rstrip())
        if result.stderr:
            output.append("[stderr]")
            output.append(result.stderr.rstrip())
        output.append(f"[exit code: {result.returncode}]")
        return "\n".join(output)

    def export_history(self, path: Path) -> str:
        payload: dict[str, Any] = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "model": self.config.model,
            "messages": self.history,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return f"Saved conversation to {path}"

    def import_history(self, path: Path) -> str:
        if not path.exists():
            return f"History file not found: {path}"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return f"Could not read history: {exc}"

        messages = data.get("messages")
        if not isinstance(messages, list):
            return "Invalid history format: missing `messages` list"
        if not messages:
            return "History file contains no messages"

        valid = all(
            isinstance(item, dict)
            and isinstance(item.get("role"), str)
            and isinstance(item.get("content"), str)
            for item in messages
        )
        if not valid:
            return "Invalid history format: malformed message entries"

        self.history = messages
        self._trim_history()
        return f"Loaded conversation from {path}"

    def _trim_history(self) -> None:
        max_messages = max(2, self.config.max_history_messages)
        if len(self.history) <= max_messages:
            return

        system = self.history[0]
        tail = self.history[-(max_messages - 1) :]
        self.history = [system, *tail]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Jarvis-like assistant using OpenAI API")
    parser.add_argument("--model", default="gpt-4.1-mini", help="Model to use")
    parser.add_argument(
        "--allow-shell",
        action="store_true",
        help="Allow local shell commands with /run <command>",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=20,
        help="Timeout for /run commands in seconds",
    )
    parser.add_argument(
        "--max-history-messages",
        type=int,
        default=30,
        help="Max messages retained in memory (including system prompt)",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="Override the default system prompt",
    )
    return parser.parse_args(argv)


def print_help() -> None:
    print("Jarvis commands:")
    print("  /help                   Show this help")
    print("  /run <command>          Execute command if --allow-shell is enabled")
    print("  /save <file.json>       Save conversation history")
    print("  /load <file.json>       Load conversation history")
    print("  /history                Show retained history size")
    print("  exit | quit             Exit assistant")


def repl(assistant: JarvisAssistant) -> int:
    print("Jarvis is online. Type 'exit' to quit. Use /help for commands.")

    while True:
        try:
            user_input = input("you> ").strip()
        except EOFError:
            print("\nGoodbye.")
            return 0
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.")
            continue

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Jarvis> Until next time.")
            return 0
        if user_input == "/help":
            print_help()
            continue
        if user_input == "/history":
            print(f"Jarvis> Stored messages: {len(assistant.history)}")
            continue
        if user_input.startswith("/save "):
            raw_path = user_input.removeprefix("/save ").strip()
            if not raw_path:
                print("Jarvis> Provide a destination file path.")
                continue
            path = Path(raw_path).expanduser()
            print(f"Jarvis> {assistant.export_history(path)}")
            continue
        if user_input.startswith("/load "):
            raw_path = user_input.removeprefix("/load ").strip()
            if not raw_path:
                print("Jarvis> Provide a source file path.")
                continue
            path = Path(raw_path).expanduser()
            print(f"Jarvis> {assistant.import_history(path)}")
            continue
        if user_input.startswith("/run "):
            command = user_input.removeprefix("/run ").strip()
            if not command:
                print("Jarvis> Provide a command after /run")
                continue
            print(assistant.execute_shell(command))
            continue

        answer = assistant.ask(user_input)
        print(f"Jarvis> {answer}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set.")
        print("Set it first: export OPENAI_API_KEY='your-key'")
        return 1

    try:
        assistant = JarvisAssistant(
            AssistantConfig(
                model=args.model,
                allow_shell=args.allow_shell,
                timeout_seconds=max(1, args.timeout_seconds),
                max_history_messages=max(2, args.max_history_messages),
                system_prompt=args.system_prompt,
            )
        )
    except ModuleNotFoundError:
        print("Missing dependency: openai. Install with `pip install -r requirements.txt`.")
        return 1

    return repl(assistant)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
