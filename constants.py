from enum import Enum


class Events(Enum):
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_ITEM_CREATED = "conversation.item.created"
    RESPONSE_CREATED = "response.created"
    RESPONSE_DONE = "response.done"
    AUDIO_TRANSCRIPT_DONE = "response.audio_transcript.done"
    AUDIO_DELTA = "response.audio.delta"
    AUDIO_DONE = "response.audio.done"
