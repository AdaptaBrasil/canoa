-- DROP FUNCTION canoa.vw_mgmt_user_sep__on_upd();

CREATE OR REPLACE FUNCTION canoa.vw_mgmt_user_sep__on_upd()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
declare
	dt_sec timestamp;
	id_sep_new int;
	id_sep_old int;
	id_schema int;
	dsc varchar(140);
	sep_new varchar(100);
	fullname varchar(201); -- string with new schema/sep
	user_using_it varchar;
	msg varchar;
	part text[];
begin
	-- mgd 2024-10-25, 11-08
	sep_new = Null;
	dt_sec = now();
	if NEW.scm_sep_new is Null or trim(NEW.scm_sep_new) = '' then
		-- remove SEP from user
		id_sep_new := Null;
	else
		-- find sep's id for the new schema_name/sep_name
		fullname := trim(NEW.scm_sep_new);
		select sep_id into id_sep_new from canoa.vw_scm_sep as vw where (vw.sep_fullname_lower = lower(fullname));

		if (id_sep_new is not Null) then
			select username into user_using_it from users where mgmt_sep_id = id_sep_new and not id = NEW.user_id;
			if user_using_it is not Null then
 				raise exception '[^|O SEP "%" está atualmente atribuído a %. Por favor, remova-o dele primeiro.|^]', fullname, user_using_it;
			end if;
		else -- if not found:
			-- add a new sep_name into table sep
			-- fullname = schema_name/sep_name => find the schema's id => schema_name = part[1]
			part := string_to_array(fullname, '/');
			sep_new = part[2];

			select id into id_schema from canoa.vw_schema as vw where (vw.name_lower = lower(part[1]));
			if id_schema is Null then
				raise exception '[^|O esquema `%` não foi encontrado.|^]', part[1];
			end if;

			-- set user name into new SEP´s description (just to inform)
			dsc := substring(('ins para ' || NEW.user_name) from 1 for 140);

			-- insert the new SEP name = part[2] and get it's id (id_sep_new)
			insert into canoa.sep
				   	   (id_schema, name,    description, visible, ins_at, ins_by)
	    		values (id_schema, sep_new, dsc,         False,   dt_sec, NEW.assigned_by)
	    		returning id into id_sep_new;

		end if;
	end if;



	-- get the user's SEP up to this point (can be null --doesn't have one) to keep track (log it)
	select mgmt_sep_id into id_sep_old from canoa.users where id = NEW.user_id;



	-- Update canoa.users table
	update canoa.users
	set mgmt_sep_id = id_sep_new  -- can be Null (remove)
	    ,mgmt_sep_at = dt_sec
		,mgmt_batch_code = NEW.batch_code -- traceability, see log_user_sep
	where id = NEW.user_id;

	-- register operation on the log table
	insert into canoa.log_user_sep
		   		(id_users,    id_sep,     id_sep_old, sep_new, done_at, done_by,         batch_code)
		 values (NEW.user_id, id_sep_new, id_sep_old, sep_new, dt_sec,  NEW.assigned_by, NEW.batch_code);

	return NEW;

end;
$function$;
