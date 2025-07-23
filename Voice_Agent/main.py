##call twilio and redirect to deepgram- hence we use sockets
##always run ngrok and update the forwarding link from terminal to twilio as this is demo acc


import asyncio
import base64
import json
import websockets
import os
from dotenv import load_dotenv

load_dotenv()


def sts_connect():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise Exception("Deepgram api key not found")
    
    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse"
        subprotocols=["token", api_key]
    )
    return sts_ws

## phone -> Twilio -> ngrok -> server -> Deepgram (STT -> AI -> TTS) -> server -> Twilio -> phone

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


# Handles user interruptions (barge-in events) from Twilio.
async def handle_barge_in(decoded, twilio_ws, streamsid):
    pass

# Processes transcribed text from Deepgram and sends AI responses back to Twilio.
async def handle_text_message(decoded, twilio_ws, sts_ws, streamsid):
    pass

# Sends audio from the audio_queue to the Deepgram WebSocket.
async def sts_sender(sts_ws, audio_queue):
    pass

# Receives messages (like audio) from Deepgram and forwards them to Twilio.
async def sts_receiver(sts_ws, twilio_ws, streamsid_queue):
    pass

# Receives audio from Twilio and puts it into the audio_queue.
async def twilio_receiver(twilio_ws, audio_queue, streamsid_queue):
    BUFFER_SIZE = 20 * 160 ##bitrate or audio quality, loading from twilio and loading to queue
    inbuffer = bytearray(b"")

    async for message in twilio_ws:
        try:
            data = json.loads(message)
            if data["event"] == "start":
                print("got our streamsid")
                start = data["start"]
                streamsid = start["streamSid"]
                streamsid_queue.put_nowait(streamsid)
            if data["event"] == "connected":
                continue
            if data["event"] == "media":
                media = data["media"]
                chunk = base64.b64decode(media["payload"])
                if media["track"] == "inbound":
                    inbuffer.extend(chunk)
            if data["event"] == "stop":
                break

            while len(inbuffer) >= BUFFER_SIZE:
                chunk = inbuffer[:BUFFER_SIZE]
                audio_queue.put_nowait(chunk)
                inbuffer = inbuffer[BUFFER_SIZE:]

        except:
            break




# Main handler for each incoming Twilio WebSocket connection.
async def twilio_handler(twilio_ws):
    audio_queue =asyncio.Queue()
    streamsid_queue =asyncio.Queue() ##multiple people will be calling to our phone number, so we handle it here

    async with sts_connect() as sts_ws:
        config_message = load_config()
        await sts_ws.send(json.dumps(config_message)) ##dump for converting into string

        await asyncio.wait(
            [
                asyncio.ensure_future(sts_sender(sts_ws, audio_queue)),
                asyncio.ensure_future(sts_receiver(sts_ws, twilio_ws, streamsid_queue)),
                asyncio.ensure_future(twilio_receiver(twilio_ws, audio_queue, streamsid_queue)),
            ]
            
        )

        await twilio_ws.close()


# Main entry point for the application. Starts the WebSocket server.
async def main():
    await websockets.serve(twilio_handler, "localhost", 5000)
    print("Started Server")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())






##DOCUMENTATION: http://developers.deepgram.com/docs/twilio-and-deepgram-voice-agent