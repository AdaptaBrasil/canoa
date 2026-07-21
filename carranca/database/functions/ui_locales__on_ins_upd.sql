-- DROP FUNCTION canoa.ui_locales__on_ins_upd();

CREATE OR REPLACE FUNCTION canoa.ui_locales__on_ins_upd()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin

	-- ----------------------------------------------------------------------------------------------
	-- /!\ Keep a copy of this file updated in carranca\database\functions\ui_locales__on_ins_upd.sql
    -- ----------------------------------------------------------------------------------------------

	-- mgd 2025-03-18
    NEW.locale := lower(NEW.locale);

	return new;
end;
$function$
;

-- Permissions

ALTER FUNCTION canoa.ui_locales__on_ins_upd() OWNER TO canoa_power;
GRANT ALL ON FUNCTION canoa.ui_locales__on_ins_upd() TO canoa_power;

-- eof
