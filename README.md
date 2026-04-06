<a href="https://livekit.io/">
  <img src="https://raw.githubusercontent.com/livekit-examples/hello-wakeword/main/.assets/livekit-mark.png" alt="LiveKit logo" width="100" height="100">
</a>

# hello-wakeword

A minimal example of **wakeword-activated voice agents** using [LiveKit Wake Word](https://github.com/livekit/livekit-wakeword). Say "hey livekit" into your microphone and a voice agent connects to chat with you.

This project demonstrates how wakeword detection can trigger a conversational AI agent, a pattern useful for hands-free interfaces on edge devices like a Raspberry Pi.

## How It Works

The **client** runs a loop: detect wakeword → connect to a LiveKit room → stream audio bidirectionally with the agent → disconnect when done → repeat.

The **agent** is a LiveKit Agents server that joins rooms automatically and provides a voice assistant powered by Deepgram (STT), OpenAI (LLM), and Cartesia (TTS).

## Project Structure

```
hello-wakeword/
├── pyproject.toml              # Workspace root (uv workspace)
├── .env.example                # Required environment variables
├── client/                     # Wakeword detection + audio streaming
│   ├── pyproject.toml          # Client dependencies
│   ├── client.py               # Wakeword listen → connect → repeat loop
│   ├── room_session.py         # LiveKit room connection + audio I/O
│   ├── models/
│   │   └── hey_livekit.onnx    # Wakeword detection model
│   └── sounds/
│       ├── in.wav              # Entry chime (wakeword detected)
│       └── out.wav             # Exit chime (agent left)
└── agent/                      # LiveKit voice agent server
    ├── pyproject.toml          # Agent dependencies
    └── agent.py                # Agent definition + entrypoint
```

## What You Need

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** - fast Python package manager
- **A microphone and speakers** on the client device
- **A LiveKit Cloud account** (free tier available) - see setup below

## Step 1: Install Dependencies

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/livekit/hello-wakeword
cd hello-wakeword
uv sync --all-packages
```

## Step 2: Get Your LiveKit Credentials

This project uses [LiveKit's inference](https://docs.livekit.io/agents/integrations/) to access STT, LLM, and TTS services. You only need a LiveKit Cloud account, no separate API keys.

1. Go to [LiveKit Cloud](https://cloud.livekit.io/) and create a free account
2. Install the [lk CLI](https://docs.livekit.io/home/cli/setup/) and authenticate:
   ```bash
   lk cloud auth
   ```
3. Generate your `.env.local` file:
   ```bash
   lk app env
   ```
   Save the output to `.env.local` in the project root.

## Step 4: Run

### Start the agent

In one terminal, start the voice agent server:

```bash
uv run wakeword-agent dev
```

The agent registers with LiveKit and waits for rooms to join.

### Start the client

In another terminal, start the wakeword listener:

```bash
uv run wakeword-client
```

Now just say **"hey livekit"**, you'll hear a chime, and the agent will greet you. Have a conversation, and when you're done, just walk away - the agent detects silence, says goodbye, and disconnects. The client then starts listening for the wakeword again.

Press `Ctrl+C` to quit.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
