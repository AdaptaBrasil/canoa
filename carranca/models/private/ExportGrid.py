"""
 Private Models
    vw_export_files
    view with the user files to export

mgd
Equipe da Canoa -- 2025.09.02
"""

# Equipe da Canoa -- 2025

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import CanoaBaseView


class ExportGrid(CanoaBaseView):
    # Latest user data file by SEP view ()
    __tablename__ = "vw_export_data_files"

    user_id: Mapped[int | None] = mapped_column(Integer)
    sep_id: Mapped[int] = mapped_column(Integer)
    scm_id: Mapped[int] = mapped_column(Integer)

    file_origin: Mapped[str | None] = mapped_column(String(1))
    file_name: Mapped[str | None] = mapped_column(String(180))
    sep_fullname: Mapped[str] = mapped_column(String(180))

    uploaded: Mapped[datetime | None] = mapped_column(DateTime)
    report_errors: Mapped[int | None] = mapped_column(Integer)
    is_exportable: Mapped[bool] = mapped_column(Boolean)


# eof
