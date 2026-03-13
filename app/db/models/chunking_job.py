from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as PgEnum
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint

from app.db.base import BaseModel
from app.db.enum import ChunkingStatus


class ChunkingJob(BaseModel):
    __tablename__ = "chunking_jobs"

    file_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    kb_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    status: Mapped[ChunkingStatus] = mapped_column(
        PgEnum(ChunkingStatus, name="chunking_status_enum"),
        nullable=False,
        default=ChunkingStatus.queued,
    )

    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    vectorized_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


    __table_args__ = (
        UniqueConstraint(
            "kb_id",
            "file_id",
            name="uq_job_identity",
        ),
    )
