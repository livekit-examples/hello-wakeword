"""
Voice agent server - a LiveKit Agent that joins rooms created by the
wakeword client and has a voice conversation with the user.

Uses: Silero (VAD), Deepgram (STT), OpenAI (LLM), Cartesia (TTS).
"""

import asyncio
import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    UserStateChangedEvent,
    cli,
    inference,
)
from livekit.plugins import silero

load_dotenv(".env.local")
logger = logging.getLogger("wakeword-agent")
server = AgentServer()

INSTRUCTIONS = (
    "You are a friendly voice assistant for a wakeword detection demo. "
    "This demo shows how a wakeword can activate a voice agent on edge devices like a Raspberry Pi. "
    "You can answer questions and have a conversation. Keep your responses short and natural."
)


@server.rtc_session(agent_name="wakeword-agent")
async def entrypoint(ctx: JobContext):
    """Called when a new user joins a room. Sets up and starts the agent session."""

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=inference.STT("deepgram/nova-3", language="en"),
        llm=inference.LLM("openai/gpt-4.1-mini"),
        tts=inference.TTS("cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
    )

    @session.on("user_state_changed")
    def on_user_state_changed(ev: UserStateChangedEvent):
        if ev.new_state == "away":
            logger.info("User went away, shutting down")
            asyncio.create_task(_say_goodbye_and_shutdown())

    async def _say_goodbye_and_shutdown():
        await session.say("It seems you've stepped away. Goodbye!")
        session.shutdown()

    agent = Agent(instructions=INSTRUCTIONS)
    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(
        instructions="greet the user, let them know the wakeword was detected, and ask how you can help"
    )


def main():
    cli.run_app(server)


if __name__ == "__main__":
    main()
