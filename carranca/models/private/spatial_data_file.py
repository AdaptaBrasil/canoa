"""
 SpatialDataFile Table



Equipe da Canoa -- 2026


"""

# cSpell:ignore: nullable sqlalchemy


from datetime import datetime
from sqlalchemy import Text, String, Integer, DateTime, BigInteger, Computed
from sqlalchemy.orm import Mapped, mapped_column
from ..base import CanoaBaseTable


class SpatialDataFile(CanoaBaseTable):
    __tablename__ = "spatial_data_files"
    __code_seed__ = 5

    # id: in CanoaBase

    spd_name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    spd_name_lower: Mapped[str] = mapped_column(String(60), Computed(""))
    spd_description: Mapped[str] = mapped_column(String(120), nullable=True)
    spd_title: Mapped[str] = mapped_column(String(80), nullable=True)

    field_id: Mapped[str] = mapped_column(String(12), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(12), nullable=True)
    field_alt_name: Mapped[str | None] = mapped_column(String(12), nullable=True)

    original_file_name: Mapped[str] = mapped_column(String(80), nullable=True)
    file_name: Mapped[str] = mapped_column(String(140), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_crc32: Mapped[int] = mapped_column(BigInteger, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    registered_by: Mapped[int] = mapped_column(Integer, nullable=False)
    edited_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    edited_by: Mapped[int] = mapped_column(Integer, nullable=True)
    file_data: Mapped[str] = mapped_column(Text, nullable=True)


# eof
