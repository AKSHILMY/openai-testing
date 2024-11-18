import asyncio
import json
import uuid
import websocket
import pyaudio
import threading
import time
import base64

from prompts.test import realtime_api_test_adhoc_session_instructions_606
# Replace with your WebSocket URL
uri = 'ws://localhost:5000/api/clients/update/realtime/open'

# Audio stream settings
CHUNK = 1024  # Number of audio samples per chunk
FORMAT = pyaudio.paInt16  # Format of audio (16-bit PCM)
CHANNELS = 1  # Mono audio
RATE = 24000  # Sample rate (Hz)
audio_data = bytearray()
def on_error(ws, error):
    print(f"ON ERROR : {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"ON CLOSE : {close_msg}")

def on_open(ws):
    print("ON OPEN")
    # Send initial message, if any
    ws.send(json.dumps({"ai_coach_id": 606}))
    session_update_event = {
                "event_id": "session_update_event",
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": realtime_api_test_adhoc_session_instructions_606,
                    "voice": "alloy",  # does not get updated
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 2000
                    },
                    "tools": [],
                    "tool_choice": "auto",
                    "temperature": 1,
                    "max_response_output_tokens": "inf"
                }
            }
    ws.send(json.dumps(session_update_event))

def on_message(ws, message):
    data_json = json.loads(message)
    res = data_json.get('response')
    if res:
        print(f"RESPONSE : {res}")
    audio_res = data_json.get('audio_response')
    if audio_res:
        # print(f"AUDIO_RESPONSE : {audio_res}")
        audio_data.extend(base64.b64decode(audio_res))

def audio_stream(ws):
    p = pyaudio.PyAudio()
    
    # Open audio stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    print("Streaming audio...")

    try:
        while ws.keep_running:
            data = stream.read(CHUNK)
            # Encode the audio chunk in base64
            encoded_data = base64.b64encode(data).decode('utf-8')
            # Send the audio data as a JSON message
            event = {
                    "event_id": f"convo_item_{uuid.uuid4()}",
                    "type": "input_audio_buffer.append",
                    "audio": encoded_data
                }
            ws.send(json.dumps(event))
            time.sleep(0.01)  # Slight delay to simulate streaming
    except Exception as e:
        print(f"Streaming error: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def run_websocket():
    ws = websocket.WebSocketApp(uri,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    # Start the audio streaming in a separate thread to avoid blocking
    audio_thread = threading.Thread(target=audio_stream, args=(ws,))
    audio_thread.start()

    # Run WebSocket in the main thread
    ws.run_forever()

# Run the WebSocket client
run_websocket()

def save_pcm_to_wav(pcm_data, file_path, sample_rate=24000, num_channels=1, sample_width=2):
    import wave
    with wave.open(file_path, 'wb') as wave_file:
        wave_file.setnchannels(num_channels)
        wave_file.setsampwidth(sample_width)
        wave_file.setframerate(sample_rate)

        wave_file.writeframes(pcm_data)
        print(f"PCM data saved to {file_path}")

save_pcm_to_wav(audio_data, f"./test_ws_end_open_channel_{str(uuid.uuid4())}.wav")