-- DROP FUNCTION canoa.users__on_ins_upd();

CREATE OR REPLACE FUNCTION canoa.users__on_ins_upd()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
declare
	reset_recover_pw_token bool;
	new_recover_pw_token_is_empty bool;
	new_token text;
begin


	-- mgd 2024-04-18
	-- keep email lowercase
	new.email := lower(new.email);

	-- if in insert, check disabled and bye
	if (TG_OP = 'INSERT') then
		new.registered_at := now();
		if new.disabled then
			new.disabled_at := now();
		end if;
		return new;
	-- DELETE or TRUNCATE just go
	elsif (TG_OP <> 'UPDATE') then
		return new;
	end if;

	-- reset password if (bad columns names: recover_email_token => recover_pw_token
	reset_recover_pw_token := (new.recover_email_token is null) and (old.recover_email_token is not null);

	-- keep datetime of pw change
	if new.password is distinct from old.password then
		new.password_changed_at := now();
		reset_recover_pw_token := true; -- reset pw token if pw is changed
	end if;

	-- keep datetime of email change (1/2026 distinct)
	if new.email is distinct from old.email then
		new.email_changed_at := now();
		new.email_verified_at := null;
		reset_recover_pw_token := true;
	end if;

	-- keep datetime when the usew was diabled
	if new.disabled and not old.disabled then
		new.disabled_at := now();
	elsif old.disabled and not new.disabled then
		new.disabled_at := null;
	elsif not new.disabled and new.disabled_at is not null then
		new.disabled_at := null;
	end if;


	-- keep verify email token date updated
	new_token := trim(coalesce(new.verify_email_token, ''));
	-- todo check only 6 digits &
	if (new_token ~ '^[0-9]{6}$') and new.verify_email_token is distinct from old.verify_email_token then
	    new.verify_email_sent_at := now();
	    new.email_verified_at    := null;
	elsif old.verify_email_token is not null and (old.verify_email_token || '*' = new_token) then
		-- Add a * to the token to indicate me (the database) that the user successfully finished the email verification process.
	    new.email_verified_at    := now();
	    new.verify_email_sent_at := null;
	    new.verify_email_token   := null;
	elsif new_token != '' then
		-- delete junk from verify_mail token
		new.verify_email_sent_at := null;
	    new.verify_email_token := null;
	elsif new_token = '' and old.verify_email_token is not null then
  		new.verify_email_sent_at := null;
	end if;


	-- keep datetime when the recover pw token was generated
	new_recover_pw_token_is_empty = (trim(coalesce(new.recover_email_token, '')) = '');
	if (old.recover_email_token is distinct from new.recover_email_token) and not new_recover_pw_token_is_empty then
		new.recover_email_token_at := now();
	elsif new_recover_pw_token_is_empty and new.recover_email_token_at is not null then
		-- sync recover_email_token_at with recover_email_token
		reset_recover_pw_token := true;
	elsif new_recover_pw_token_is_empty and new.recover_email_token is not null then
		-- clean grabage from recover_email_token
		reset_recover_pw_token := true;
	end if;
	-- TODO check min lenght of recover_email_token

	-- not needed any more
	if reset_recover_pw_token then
		new.recover_email_token := null;
		new.recover_email_token_at := null;
	end if;

	return new;
end;
$function$
;
