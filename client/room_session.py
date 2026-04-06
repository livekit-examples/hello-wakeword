"""
LiveKit room session - connects to a room, streams mic audio to the agent,
and plays the agent's audio through the speaker. Exits when the agent leaves.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

import sounddevice as sd
import soundfile as sf
from livekit import api, rtc
from livekit.api import RoomAgentDispatch, RoomConfiguration

SOUNDS_DIR = Path(__file__).parent / "sounds"
logger = logging.getLogger("wakeword-client")

# Audio settings - 48kHz mono matches LiveKit's default audio format
SAMPLE_RATE = 48000
CHANNELS = 1


def play_sound(filename: str) -> None:
    """Play a WAV file from the sounds/ directory (non-blocking)."""
    data, samplerate = sf.read(SOUNDS_DIR / filename)
    sd.play(data, samplerate)


class RoomSession:
    """Manages a LiveKit room session with bidirectional audio.

    Usage (as async context manager):
        async with RoomSession(room_name="my-room") as session:
            await session.run()  # blocks until agent disconnects
    """

    def __init__(self, room_name: str):
        self._room_name = room_name
        self._room = rtc.Room()
        self._agent_left = asyncio.Event()  # signals when the session should end

        # Audio device manager for mic input and speaker output
        self._devices = rtc.MediaDevices(
            input_sample_rate=SAMPLE_RATE,
            output_sample_rate=SAMPLE_RATE,
            num_channels=CHANNELS,
        )
        self._mic = None
        self._player = None

    async def __aenter__(self):
        # --- Auth: create a short-lived JWT token for this room ---
        url = os.environ["LIVEKIT_URL"]
        token = (
            api.AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
            .with_identity("wakeword-user")
            .with_name("Wake Word User")
            .with_grants(api.VideoGrants(room_join=True, room=self._room_name))
            .with_room_config(
                RoomConfiguration(
                    agents=[RoomAgentDispatch(agent_name="wakeword-agent")],
                ),
            )
            .to_jwt()
        )

        # --- Open audio devices ---
        # Enable audio processing to clean up the mic signal:
        #   AEC = echo cancellation, so the agent doesn't hear itself
        #   noise suppression, high-pass filter, auto gain = cleaner audio
        self._mic = self._devices.open_input(
            enable_aec=True,
            noise_suppression=True,
            high_pass_filter=True,
            auto_gain_control=True,
        )
        self._player = self._devices.open_output()

        # --- Room event handlers ---
        @self._room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant):
            """Agent published an audio track - start playing it."""
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info("Subscribed to agent audio track")
                asyncio.create_task(self._player.add_track(track))

        @self._room.on("track_unsubscribed")
        def on_track_unsubscribed(track, publication, participant):
            """Agent removed an audio track - stop playing it."""
            asyncio.create_task(self._player.remove_track(track))

        @self._room.on("participant_disconnected")
        def on_participant_disconnected(participant):
            """Agent left the room - end the session."""
            logger.info("Participant left: %s", participant.identity)
            self._agent_left.set()

        @self._room.on("disconnected")
        def on_disconnected():
            """We got disconnected from the room."""
            logger.info("Room disconnected")
            self._agent_left.set()

        # --- Agent event stream: detect when agent marks user as "away" ---
        # The agent sends structured events over a text stream. We watch for
        # the "user_state_changed" event with state "away" (meaning the user
        # has been silent too long), which tells us the agent is about to leave.
        async def _read_agent_events(reader, participant_identity):
            async for chunk in reader:
                try:
                    event = json.loads(chunk)
                    if event.get("type") == "user_state_changed" and event.get("new_state") == "away":
                        logger.info("User marked as away")
                        self._agent_left.set()
                except json.JSONDecodeError:
                    pass

        self._room.register_text_stream_handler(
            "lk.agent.events",
            lambda reader, pid: asyncio.create_task(_read_agent_events(reader, pid)),
        )

        # --- Connect and publish mic ---
        await self._room.connect(url, token)
        logger.info("Connected to room: %s", self._room.name)

        # Create an audio track from the mic and publish it so the agent can hear us
        track = rtc.LocalAudioTrack.create_audio_track("microphone", self._mic.source)
        opts = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        await self._room.local_participant.publish_track(track, opts)
        logger.info("Published mic track")

        # Start the speaker output
        await self._player.start()
        return self

    async def run(self):
        """Block until the agent leaves the room."""
        await self._agent_left.wait()
        logger.info("Agent left - ending session")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up: close audio devices and disconnect from the room."""
        if self._player:
            await self._player.aclose()
        if self._mic:
            await self._mic.aclose()
        await self._room.disconnect()
        logger.info("Cleaned up room session")
