-- DROP FUNCTION canoa.users__on_ins_upd();

CREATE OR REPLACE FUNCTION canoa.users__on_ins_upd()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
declare
	new_token text;
    is_setting_new_token bool;
	reset_recover_pw_token bool;
	new_recover_pw_token_is_empty bool;
begin

	-- -----------------------------------------------------------------------------------------
	-- /!\ Keep a copy of this file updated in carranca\database\functions\users__on_ins_upd.sql
    -- ------------------------------------------------------------------------------------------
    -- mgd version 2026.08.19

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

	-- keep datetime when the user was disabled
	if new.disabled and not old.disabled then
		new.disabled_at := now();
	elsif old.disabled and not new.disabled then
		new.disabled_at := null;
	elsif not new.disabled and new.disabled_at is not null then
		new.disabled_at := null;
	end if;


	-- keep verify email token date updated
	-- NOTE: this trigger fires on ANY update to the users row, not just ones about e-mail
	-- verification -- every branch below must check "distinct from old" before acting, or
	-- it'll misfire on an untouched-but-still-pending token from an unrelated column change.
	new_token := trim(coalesce(new.verify_email_token, ''));
    is_setting_new_token = new.verify_email_token is distinct from old.verify_email_token;

	if is_setting_new_token and (new_token ~ '^[0-9]{6}$') then
        -- new_token is a valid 6-digit token
        -- verification process has started, stamp when the email was sent.
	    new.verify_email_sent_at := now();
	    new.email_verified_at    := null;
	elsif old.verify_email_token is not null and (old.verify_email_token || '*' = new_token) then
		-- Add a * to the token to indicate me (the database) that the user successfully finished the email verification process.
	    new.email_verified_at    := now();
	    new.verify_email_sent_at := null;
	    new.verify_email_token   := null;
	elsif is_setting_new_token and new_token != '' then
		-- Invalid token, keep table row safe:
		new.verify_email_sent_at := null;
	    new.verify_email_token := null;
	elsif new_token = '' and old.verify_email_token is not null then
		-- token explicitly cleared to null/empty in this same statement
        -- and one used to exist
        -- -> sync sent_at to null too, so nothing pending is left dangling.
  		new.verify_email_sent_at := null;
	end if;


	-- a real login just happened -> clear any pending "forgot password" request
	if new.last_login_at is not null and new.last_login_at is distinct from old.last_login_at then
		reset_recover_pw_token := true;
		new.password_failures := 0;
	end if;

	-- keep datetime when the recover pw token was generated
	new_recover_pw_token_is_empty = (trim(coalesce(new.recover_email_token, '')) = '');
	if (old.recover_email_token is distinct from new.recover_email_token) and not new_recover_pw_token_is_empty then
		new.recover_email_token_at := now();
	elsif new_recover_pw_token_is_empty and new.recover_email_token_at is not null then
		-- sync recover_email_token_at with recover_email_token
		reset_recover_pw_token := true;
	elsif new_recover_pw_token_is_empty and new.recover_email_token is not null then
		-- clean garbage from recover_email_token
		reset_recover_pw_token := true;
	end if;
	-- TODO check min length of recover_email_token

	if reset_recover_pw_token then
		-- not needed any more
		new.recover_email_token := null;
		new.recover_email_token_at := null;
	end if;

	return new;
end;
$function$
;

-- Permissions

ALTER FUNCTION canoa.users__on_ins_upd() OWNER TO canoa_power;
GRANT ALL ON FUNCTION canoa.users__on_ins_upd() TO canoa_power;

-- eof