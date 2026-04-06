# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

hello-wakeword is a Python wakeword detection project. It uses Python 3.12 and uv workspaces with two members:

- **client/** - TUI wakeword detector (Textual app, LiveKit room client)
- **agent/** - LiveKit voice agent server

## Strict Rules

- **Always use uv** - never use pip, pip install, python -m pip, or any other package manager. All dependency management and script execution must go through uv (e.g., `uv add`, `uv run`, `uv sync`).
- **Always use git** - never make changes without proper version control. Commit frequently with clear messages. Do not use `--no-verify` or skip hooks.

## Commands

- **Run client**: `uv run wakeword-client`
- **Run agent**: `uv run wakeword-agent dev`
- **Add dependency**: `uv add --package <member> <package>`
- **Sync environment**: `uv sync --all-packages`
