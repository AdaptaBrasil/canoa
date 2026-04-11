-- DROP FUNCTION canoa.vw_mgmt_seps_user__on_upd();

CREATE OR REPLACE FUNCTION canoa.vw_mgmt_seps_user__on_upd()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
declare
	done_at timestamp;
	usr_new_name varchar(100);
    usr_curr_id int;
	usr_new_id int;
    operation char(1); -- mgd 2025-06-28 (S)et, (R)emoved | (E)dited, Marked as (D)eleted. For insert, see sep.ins_at.
begin
    -- spell:ignore mgmt plpgsql

	-- /!\ Keep a copy of this file updated in carranca\private\seps_mgmt\vw_mgmt_seps_user__on_upd.sql

    -- TODO:
    -- Get message string from vw_ui_texts

	usr_new_name = Null;
	done_at = now();
	if NEW.id is Null then
 		raise exception '[^|ID do SEP não foi informado.|^]';
    end if;
    -- save the current sep's ID
    select user_id into usr_curr_id from vw_mgmt_seps_user where id = NEW.id;

	if NEW.user_new is Null or trim(NEW.user_new) = '' then
		-- remove user's SEP
        if usr_curr_id is Null then
            return NEW; -- ignore, there in no current user
		end if;
		operation := 'R';
		usr_new_id := Null;

	else -- find the user's ID from their name
		usr_new_name:= trim(NEW.user_new);
		select id into usr_new_id from canoa.users as usr where (usr.username_lower = lower(usr_new_name));
		operation:= 'S';
		if (usr_new_id is Null) then
 			raise exception '[^|Não foi encontrado o registro do usuário "%".|^]', usr_new_name;
		elsif usr_curr_id is Null then
            -- OK, no current user!
		elsif usr_curr_id = usr_new_id then
            return NEW; -- ignore, the new user is the same as the current user.
		end if;
	end if;


	-- Update canoa.sep table
	update canoa.sep
        set mgmt_users_id = usr_new_id
            ,mgmt_users_at = done_at
            ,mgmt_batch_code = NEW.batch_code -- traceability, see log_user_sep
        where id = NEW.id;

	-- register operation on the log table
	insert into canoa.log_user_sep
		   		(id_users,    id_sep, id_users_prior, done_at, done_by,         batch_code,     operation)
		 values (usr_new_id,  NEW.id, usr_curr_id,    done_at, NEW.assigned_by, NEW.batch_code, operation);

	return NEW;

end;
$function$
;
