##call twilio and redirect to deepgram- hence we use sockets
##always run ngrok and update the forwarding link from terminal to twilio as this is demo acc
import asyncio
import base64
import json
import websockets
import os
from dotenv import load_dotenv

from pharmacy_functions import FUNCTION_MAP

load_dotenv()


def sts_connect():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise Exception("Deepgram api key not found")
    
    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", api_key]
    )
    return sts_ws

## phone -> Twilio -> ngrok -> server -> Deepgram (STT -> AI -> TTS) -> server -> Twilio -> phone

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


# Handles user interruptions (barge-in events) from Twilio.
async def handle_barge_in(decoded, twilio_ws, streamsid):
    if decoded["type"] == "UserStartedSpeaking":
        clear_message = {
            "event": "clear",
            "streamSid": streamsid
        }
        await twilio_ws.send(json.dumps(clear_message))


def execute_function_call(func_name, arguments):
    if func_name in FUNCTION_MAP:
        result = FUNCTION_MAP[func_name](**arguments)
        print(f"Function call result: {result}")
        return result
    else:
        result = {"error": f"Unknown function:{func_name}"}
        print(result)
        return result


def create_function_call_response(func_id, func_name, result): ##gotta pass formatted message to deepgram from our function call
    return{
        "type":"FunctionCallResponse",
        "id": func_id,
        "name": func_name,
        "content": json.dumps(result)
    }


async def handle_function_call_request(decoded, sts_ws):
    try:
        for function_call in decoded["functions"]:
            func_name = function_call["name"]
            func_id = function_call["id"]
            arguments = json.loads(function_call["arguments"])

            print(f"Function call:{func_name} (ID:{func_id}), arguments: {arguments}")

            result = execute_function_call(func_name, arguments)

            function_result = create_function_call_response(func_id, func_name,result)

            await sts_ws.send(json.dumps(function_result))
            print(f"Sent function result: {function_result}")



    except Exception as e:
        print(f"Error calling function: {e}")
        error_result = create_function_call_response(
            func_id if "func_id" in locals() else "unknown",
            func_name if "func_name" in locals() else "unknown",
            {"error": f"Function call failed with: {str(e)}"}
        )

        await sts_ws.send(json.dumps(error_result))




# Processes transcribed text from Deepgram and sends AI responses back to Twilio.
async def handle_text_message(decoded, twilio_ws, sts_ws, streamsid):
    await handle_barge_in(decoded, twilio_ws, streamsid)

    if decoded["type"] == "FunctionCallRequest":
        await handle_function_call_request(decoded,sts_ws)

# Sends audio from the audio_queue to the Deepgram WebSocket.
async def sts_sender(sts_ws, audio_queue):
    print("sts_sender started")
    while True:
        chunk = await audio_queue.get()
        await sts_ws.send(chunk) ##sending from twilio to deepgram




# Receives messages (like audio) from Deepgram and forwards them to Twilio.
async def sts_receiver(sts_ws, twilio_ws, streamsid_queue):
    print("sts_receiver started")
    streamsid = await streamsid_queue.get()

    async for message in sts_ws:
        ##loading data from deepgram. consists of new resposne text/speech
        if type(message) is str:
            print(message)
            decoded = json.loads(message)
            await handle_text_message(decoded, twilio_ws, sts_ws, streamsid)
            continue

        raw_mulaw = message
  
            ##once we get bytes/audio from deepgram, we've to send to twilio
        media_message = {
            "event" : "media",
            "streamSid": streamsid,
            'media': {"payload": base64.b64encode(raw_mulaw).decode("ascii")}
        }

        await twilio_ws.send(json.dumps(media_message))


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
                chunk = inbuffer[:BUFFER_SIZE] ##not to send the audio immediately, but send it periodical
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