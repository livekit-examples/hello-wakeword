"""
Wakeword detection client - listens for "hey livekit", then connects
to a LiveKit room to talk with a voice agent. Loops forever.
"""

import asyncio
import logging
import uuid
from pathlib import Path

from dotenv import load_dotenv

from room_session import RoomSession, play_sound

# Path to the ONNX wakeword model bundled with this package
MODELS_DIR = Path(__file__).parent / "models"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("wakeword-client")


async def wait_for_wakeword() -> None:
    """Block until the user says "hey livekit".

    Uses the livekit-wakeword library with a local ONNX model.
    - threshold: minimum confidence score to accept a detection (0-1)
    - debounce: seconds to wait before accepting another detection
    """
    from livekit.wakeword import WakeWordListener, WakeWordModel

    model = WakeWordModel(models=[str(MODELS_DIR / "hey_livekit.onnx")])

    print('\nListening for "hey livekit"...')
    async with WakeWordListener(model, threshold=0.5, debounce=1.5) as listener:
        detection = await listener.wait_for_detection()
        print(f"  Detected ({detection.confidence:.0%})")


async def main_loop() -> None:
    """Main loop: detect wakeword → join room → talk → repeat."""
    while True:
        # Step 1: Wait for the user to say the wakeword
        await wait_for_wakeword()

        # Step 2: Play entry chime and pause briefly
        play_sound("in.wav")
        await asyncio.sleep(1.5)

        # Step 3: Connect to a new LiveKit room and talk with the agent
        try:
            room_name = f"wakeword-{uuid.uuid4().hex[:8]}"
            print(f"\nConnecting to room {room_name}...")
            async with RoomSession(room_name=room_name) as session:
                print("Connected - speaking with agent...")
                await session.run()  # blocks until agent leaves
            print("Agent left.")
        except Exception:
            logger.exception("Room session error")

        # Step 4: Play exit chime and pause before looping back
        play_sound("out.wav")
        await asyncio.sleep(1.5)


def main():
    load_dotenv(".env.local")
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()
