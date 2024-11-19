import asyncio
import json
import uuid
import websocket
import pyaudio
import threading
import time
import base64

uri = 'ws://localhost:5000/api/clients/update/realtime/open/final'

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
    config = {
        "ai_coach_id": 606,
        "silence_duration_ms" : 2000,
        "voice" : "alloy"
        }
    ws.send(json.dumps(config))

def on_message(ws, message):
    event_json = json.loads(message)
    match event_json.get("type"):
        case "response_text":
            text = event_json.get("text","")
            print(f"<response_text> : {text}")
        case "response_audio_delta":
            audio_delta = event_json.get("audio",b'')
            print(f"<response_audio_delta>")
            audio_data.extend(base64.b64decode(audio_delta))
        case _ :
            raise Exception(f"No such event : {message}")

def audio_stream(ws):
    p = pyaudio.PyAudio()

    # Open audio stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    time.sleep(5)
    print("Streaming audio...")

    try:
        while ws.keep_running:
            data = stream.read(CHUNK)
            # Encode the audio chunk in base64
            encoded_data = base64.b64encode(data).decode('utf-8')
            # Send the audio data as a JSON message
            audio_chunk_input_event = {
                    "event_id": f"input_audio_buffer_item_{uuid.uuid4()}",
                    "type": "input_audio_buffer.append",
                    "audio": encoded_data
                }
            ws.send(json.dumps(audio_chunk_input_event))

            # Introduce a pause for 30 seconds (simulate stop)
            time.sleep(0.01)  # Slight delay to simulate normal streaming

            # Pause recording for 30 seconds
            if time.time() % 60 < 30:  # Pause every 60 seconds for 30 seconds
                print("Pausing recording for 30 seconds...")
                # Stop the stream and release resources
                stream.stop_stream()
                stream.close()

                # Wait for 30 seconds (simulate pause)
                time.sleep(30)

                # Reopen the stream after 30 seconds
                print("Resuming recording...")
                stream = p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)

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