import enum


class ChunkingStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    processed = "processed"
    failed = "failed"
    canceled = "canceled"
