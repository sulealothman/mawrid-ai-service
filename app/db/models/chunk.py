from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, Text, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import UniqueConstraint
from sqlalchemy import DateTime


from app.db.base import BaseModel


class Chunk(BaseModel):
    __tablename__ = "chunks"

    file_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    kb_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    page: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    vectorized_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    chunking_version: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        Index("ix_chunks_file_chunk", "file_id", "chunk_index"),
        UniqueConstraint(
            "kb_id",
            "file_id",
            "page",
            "chunk_index",
            "chunking_version",
            name="uq_chunk_identity",
        ),
    )
