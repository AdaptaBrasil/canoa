"""
SEP Management and User assignment
Database Column Names & Cargo Keys (data sent from the front-end)

Equipe da Canoa — 2025
mgd 2025-04-17
"""

# cSpell: ignore mgmt
from ...models.private import MgmtSepsUser


class SepMgmtGridCols:
    # This class defines the columns that are sent to and used in `sep_mgmt``.
    sep_id = MgmtSepsUser.id.name  # Column 0  - hidden
    # computed col from icon_file_name, see private/sep_mgmt/seps_grid.py._sep_data_fetch
    icon_url = MgmtSepsUser.icon_file_name.name  # 1 - hidden
    usr_curr = MgmtSepsUser.user_curr.name  # 2 - hidden
    sep_fn = MgmtSepsUser.fullname.name  # 3
    usr_new = MgmtSepsUser.user_new.name  # 4
    set_at = MgmtSepsUser.assigned_at.name  # 5
    visible = MgmtSepsUser.visible.name  # 6


class CargoKeys:
    # TODO refactor to avoid confusion with 
    # This class is used to create the cargo of the response of `sp_mgmt` & etc
    # and parsed sep_mgm_save._prepare_data_to_save
    actions = "actions"
    cargo = "cargo"
    none = "none"


# eof
