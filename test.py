import asyncio
import base64
import json
import uuid
import websockets


async def send_periodic_message(uri):
    audio_clients_path = ["./resources/client/client1.wav", "./resources/client/client2.wav"]
    def audio_d(file_path,id: str, prev_id: str = None,role : str = "user"):
        from pydub import AudioSegment
        import io
        def audio_to_item_create_event(audio_bytes: bytes, id: str, prev_id: str = None,role : str = "user") -> str:
            # Load the audio file from the byte stream
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Resample to 24kHz mono pcm16
            pcm_audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2).raw_data
            
            # Encode to base64 string
            pcm_base64 = base64.b64encode(pcm_audio).decode()
            
            event = {
                "event_id": f"convo_item_{uuid.uuid4()}",
                "type": "conversation.item.create",
                "previous_item_id": prev_id,
                "item": {
                    "id": id,
                    "type": "message",
                    "role": role,
                    "content": [
                        {
                            "type": "input_audio",
                            "audio": pcm_base64
                        }
                    ]
                }
            }
            return json.dumps(event)
        audio = AudioSegment.from_file(file_path, format="wav")

        audio_bytes = io.BytesIO()
        audio.export(audio_bytes, format="wav")
        audio_bytes = audio_bytes.getvalue()
    

        # Use audio_bytes for creating the event
        audio_event = audio_to_item_create_event(audio_bytes,id, prev_id,role)
        return audio_event
    
    async with websockets.connect(uri) as websocket:
        i = 0
        while i<len(audio_clients_path):
            await asyncio.sleep(2)
            message = json.dumps({
                "event_id": "convo_item_0",
                "type": "conversation.item.create",
                "previous_item_id": None,
                "item": {
                    "id": 1,
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "text": audio_d(file_path=audio_clients_path[i],id=str(i),prev_id=str(i-1))
                        }
                    ]
                }
            })  # Replace this with your desired message
            await websocket.send(message)
            i+=1
            await asyncio.sleep(1)
            message = json.dumps({
                "event_id": "event_234",
                "type": "response.create",
                "response": {
                    "modalities": ["text"],  # , "audio"],
                    "instructions": "Respond as a coach and prepend 'Coach:' to the response. The response should always be a string",
                    "voice": "alloy",
                    "output_audio_format": "pcm16",
                    "tools": [],
                    "tool_choice": "auto",
                    "temperature": 1,
                    "max_output_tokens": "inf"
                }
            })
            await websocket.send(message)
            await asyncio.sleep(5)

# Replace 'ws://your-websocket-endpoint' with your WebSocket URL
uri = 'ws://localhost:5000/api/clients/update/realtime'

# Run the WebSocket client
asyncio.run(send_periodic_message(uri))
