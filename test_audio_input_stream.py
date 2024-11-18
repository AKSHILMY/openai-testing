import asyncio
import base64
import json
import uuid
import websockets
from prompts.test import realtime_api_test_adhoc_session_instructions_606
from pydub import AudioSegment
import io

async def send_periodic_message(uri):
    audio_clients_path = ["./resources/client/client1_sil.wav", "./resources/client/client2_sil.wav"]
    
    def audio_to_chunked_events(file_path, chunk_duration=1000, id: str = None, prev_id: str = None, role: str = "user"):
        """
        Splits the audio file into chunks and returns a generator of events for each chunk.
        
        :param file_path: Path to the audio file
        :param chunk_duration: Duration of each audio chunk in milliseconds (e.g., 1000 ms = 1 second)
        :param id: Unique identifier for the message
        :param prev_id: Previous item id in the conversation
        :param role: Role of the sender ("user" by default)
        :return: A generator yielding events for each audio chunk
        """
        audio = AudioSegment.from_file(file_path, format="wav")
        total_duration = len(audio)
        num_chunks = (total_duration // chunk_duration) + 1  # Calculate the number of chunks

        for chunk_num in range(num_chunks):
            start_time = chunk_num * chunk_duration
            end_time = min((chunk_num + 1) * chunk_duration, total_duration)
            audio_chunk = audio[start_time:end_time]
            
            # Resample to 24kHz mono PCM16 and convert to base64
            pcm_audio = audio_chunk.set_frame_rate(24000).set_channels(1).set_sample_width(2).raw_data
            pcm_base64 = base64.b64encode(pcm_audio).decode()
            
            # Create event for this chunk
            event = {
                    "event_id": f"convo_item_{uuid.uuid4()}",
                    "type": "input_audio_buffer.append",
                    "audio": pcm_base64
                }
            yield json.dumps(event)
    
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"ai_coach_id": 606}))
        await asyncio.sleep(1)
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
        await websocket.send(json.dumps(session_update_event))

        for i, file_path in enumerate(audio_clients_path):
            id = input("ID for audio session: ")
            prev_id = input("Prev ID (leave blank if none): ")
            # Send audio chunks for each file
            for chunk_message in audio_to_chunked_events(file_path, id=id, prev_id=prev_id, role="user"):
                await websocket.send(chunk_message)
            await asyncio.sleep(5)

            # await websocket.send(json.dumps({
            #         "event_id": f"convo_item_{uuid.uuid4()}",
            #         "type": "input_audio_buffer.commit",
            #     }))
            # Send response request after all chunks of this audio file
            # response_message = json.dumps({
            #     "event_id": f"event_{uuid.uuid4()}",
            #     "type": "response.create",
            #     "response": {
            #         "modalities": ["text", "audio"],
            #         "instructions": realtime_api_test_adhoc_session_instructions_606,
            #         "voice": "alloy",
            #         "output_audio_format": "pcm16",
            #         "tools": [],
            #         "tool_choice": "auto",
            #         "temperature": 1,
            #         "max_output_tokens": "inf"
            #     }
            # })
            # await websocket.send(response_message)
            await asyncio.sleep(5)  # Wait for response processing

# Replace 'ws://your-websocket-endpoint' with your WebSocket URL
uri = 'ws://localhost:5000/api/clients/update/realtime'

# Run the WebSocket client
asyncio.run(send_periodic_message(uri))
