-- DROP FUNCTION canoa.vw_ui_texts__on_upd();

CREATE OR REPLACE FUNCTION canoa.vw_ui_texts__on_upd()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin

    -- ----------------------------------------------------------------------------------------
    -- /!\ Keep a copy of this file updated in carranca\database\functions\vw_ui_texts__on_upd.sql
    -- ----------------------------------------------------------------------------------------

    -- mgd 2026-07-28: only `item` (ui_items.name) and `text` (ui_items.text) are editable
    -- through this view -- section/locale/kind come from the joined tables, not touched here.
    if NEW.id is Null then
        raise exception '[^|ID do texto não foi informado.|^]';
    end if;

    update canoa.ui_items
        set name = NEW.item
            ,text = NEW.text
        where id = NEW.id;

    return NEW;

end;
$function$
;

-- Permissions

ALTER FUNCTION canoa.vw_ui_texts__on_upd() OWNER TO canoa_power;
GRANT ALL ON FUNCTION canoa.vw_ui_texts__on_upd() TO canoa_power;

-- eof
