-- DROP FUNCTION canoa.user_data_files__on_ins_upd();

CREATE OR REPLACE FUNCTION canoa.user_data_files__on_ins_upd()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
declare
	reset_pw_token bool;
	db_version varchar(8);
begin

	-- ---------------------------------------------------------------------------------------------------
	-- /!\ Keep a copy of this file updated in carranca\database\functions\user_data_files__on_ins_upd.sql
    -- ---------------------------------------------------------------------------------------------------

	if (TG_OP = 'INSERT') then
		-- can be used to check if remote has other time zone (compare to d_register_started_at)
		new.registered_at := now();
		select number into db_version from canoa.db_version order by id desc limit 1;
		new.db_version := db_version;
	elsif (TG_OP <> 'UPDATE') then
		return new;
	end if;

	if (NEW.email_sent AND not OLD.email_sent) then
		new.email_sent_at := now();
	end if;

	if (NEW.error_code is not null AND NEW.error_code <> 0 AND OLD.error_code is null) then
		new.error_at := now();
	end if;


	if (NEW.error_code = 0 AND NEW.success_text is not null
		AND (OLD.success_text is null OR OLD.error_code is distinct from 0)) then
		-- Record the file successful validation as a movement in the log: 'V' = Validado  2026.07.23
		insert into canoa.log_user_sep (id_sep, done_by, done_at, operation, batch_code, id_user_data_files)
		values (NEW.id_sep, NEW.id_users, now(), 'V', NEW.id::text, NEW.id);
	end if;

	return new;
end;
$function$
;

-- Permissions

ALTER FUNCTION canoa.user_data_files__on_ins_upd() OWNER TO canoa_power;

GRANT ALL ON FUNCTION canoa.user_data_files__on_ins_upd() TO public;
GRANT ALL ON FUNCTION canoa.user_data_files__on_ins_upd() TO canoa_power;

-- eof