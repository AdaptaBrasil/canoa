"""
 SpatialDataFile Table



Equipe da Canoa -- 2026


"""

# cSpell:ignore: nullable sqlalchemy


from datetime import datetime
from sqlalchemy import Text, String, Integer, DateTime, Computed, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from ..base import CanoaBaseTable


class SpatialDataFile(CanoaBaseTable):
    __tablename__ = "spatial_data_files"
    __table_args__ = {"schema": "canoa"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    file_name: Mapped[str] = mapped_column(String(140), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_crc32: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ticket: Mapped[str] = mapped_column(String(40), nullable=False)
    ticket_lower: Mapped[str | None] = mapped_column(String(40), Computed("lower(ticket)", persisted=True))
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    registered_by: Mapped[int] = mapped_column(Integer, ForeignKey("canoa.users.id"))
    edited_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    edited_by: Mapped[int] = mapped_column(Integer, ForeignKey("canoa.users.id"), nullable=False)
    error_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    success_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    log_file_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    spd_name: Mapped[str] = mapped_column(String(80), nullable=False)
    spd_name_lower: Mapped[str | None] = mapped_column(String(80), Computed("lower(spd_name)", persisted=True))
    spd_description: Mapped[str] = mapped_column(String(80), nullable=False)


# eof
