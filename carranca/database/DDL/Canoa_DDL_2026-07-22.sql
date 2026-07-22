-- DROP SCHEMA canoa;

CREATE SCHEMA canoa AUTHORIZATION canoa_power;

-- DROP SEQUENCE canoa.db_version__id_seq;

CREATE SEQUENCE canoa.db_version__id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.db_version__id_seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.db_version__id_seq TO canoa_power;

-- DROP SEQUENCE canoa.log_user_sep__id_seq;

CREATE SEQUENCE canoa.log_user_sep__id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.log_user_sep__id_seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.log_user_sep__id_seq TO canoa_power;
GRANT USAGE ON SEQUENCE canoa.log_user_sep__id_seq TO canoa_connstr;

-- DROP SEQUENCE canoa.roles__id_seq;

CREATE SEQUENCE canoa.roles__id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.roles__id_seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.roles__id_seq TO canoa_power;

-- DROP SEQUENCE canoa.schema_id__seq;

CREATE SEQUENCE canoa.schema_id__seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.schema_id__seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.schema_id__seq TO canoa_power;
GRANT USAGE ON SEQUENCE canoa.schema_id__seq TO canoa_connstr;

-- DROP SEQUENCE canoa.sep_id__seq;

CREATE SEQUENCE canoa.sep_id__seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.sep_id__seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.sep_id__seq TO canoa_power;
GRANT USAGE ON SEQUENCE canoa.sep_id__seq TO canoa_connstr;

-- DROP SEQUENCE canoa.spatial_data_files_id__seq;

CREATE SEQUENCE canoa.spatial_data_files_id__seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.spatial_data_files_id__seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.spatial_data_files_id__seq TO canoa_power;
GRANT USAGE ON SEQUENCE canoa.spatial_data_files_id__seq TO canoa_connstr;

-- DROP SEQUENCE canoa.ui_items__id_seq;

CREATE SEQUENCE canoa.ui_items__id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.ui_items__id_seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.ui_items__id_seq TO canoa_power;

-- DROP SEQUENCE canoa.ui_kinds__id_seq;

CREATE SEQUENCE canoa.ui_kinds__id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.ui_kinds__id_seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.ui_kinds__id_seq TO canoa_power;

-- DROP SEQUENCE canoa.ui_locales__id_seq;

CREATE SEQUENCE canoa.ui_locales__id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.ui_locales__id_seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.ui_locales__id_seq TO canoa_power;

-- DROP SEQUENCE canoa.ui_sections__id_seq;

CREATE SEQUENCE canoa.ui_sections__id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.ui_sections__id_seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.ui_sections__id_seq TO canoa_power;

-- DROP SEQUENCE canoa.user_data_files__id_seq;

CREATE SEQUENCE canoa.user_data_files__id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.user_data_files__id_seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.user_data_files__id_seq TO canoa_power;
GRANT USAGE ON SEQUENCE canoa.user_data_files__id_seq TO canoa_connstr;

-- DROP SEQUENCE canoa.users__id_seq;

CREATE SEQUENCE canoa.users__id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE canoa.users__id_seq OWNER TO canoa_power;
GRANT ALL ON SEQUENCE canoa.users__id_seq TO canoa_power;
GRANT USAGE, SELECT ON SEQUENCE canoa.users__id_seq TO canoa_connstr;
-- canoa.db_version definition

-- Drop table

-- DROP TABLE canoa.db_version;

CREATE TABLE canoa.db_version (
	id int4 DEFAULT nextval('db_version__id_seq'::regclass) NOT NULL,
	"number" varchar(8) NOT NULL, -- Format: Major (new table), Minor (new columnn), Bug fix/small correction.
	app_version varchar(8) NULL, -- The application version at the time this record was created.
	description varchar(200) NOT NULL, -- Stores important revisions and modifications.
	applied_at timestamp DEFAULT CURRENT_TIMESTAMP NULL, -- Readonly column that stores the date time of creation.
	CONSTRAINT db_version__number_uix UNIQUE (number),
	CONSTRAINT db_version__pk PRIMARY KEY (id)
);

-- Column comments

COMMENT ON COLUMN canoa.db_version."number" IS 'Format: Major (new table), Minor (new columnn), Bug fix/small correction.';
COMMENT ON COLUMN canoa.db_version.app_version IS 'The application version at the time this record was created.';
COMMENT ON COLUMN canoa.db_version.description IS 'Stores important revisions and modifications.';
COMMENT ON COLUMN canoa.db_version.applied_at IS 'Readonly column that stores the date time of creation.';

-- Permissions

ALTER TABLE canoa.db_version OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.db_version TO canoa_power;
GRANT SELECT ON TABLE canoa.db_version TO canoa_connstr;


-- canoa.roles definition

-- Drop table

-- DROP TABLE canoa.roles;

CREATE TABLE canoa.roles (
	id int4 DEFAULT nextval('roles__id_seq'::regclass) NOT NULL,
	"name" varchar(64) NOT NULL,
	description varchar(200) NOT NULL,
	name_lower varchar(64) GENERATED ALWAYS AS (lower(name::text)) STORED NULL,
	abbr varchar(3) NOT NULL, -- DO NOT ALTER, Is 3-letter identifier of the user's role to simplify coding permissions.
	CONSTRAINT roles__abbr_uix UNIQUE (abbr),
	CONSTRAINT roles__name_lower_uix UNIQUE (name_lower),
	CONSTRAINT roles__name_uix UNIQUE (name),
	CONSTRAINT roles__pk PRIMARY KEY (id)
);

-- Column comments

COMMENT ON COLUMN canoa.roles.abbr IS 'DO NOT ALTER, Is 3-letter identifier of the user''s role to simplify coding permissions.';

-- Permissions

ALTER TABLE canoa.roles OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.roles TO canoa_power;
GRANT SELECT ON TABLE canoa.roles TO canoa_connstr;


-- canoa.ui_kinds definition

-- Drop table

-- DROP TABLE canoa.ui_kinds;

CREATE TABLE canoa.ui_kinds (
	id int4 DEFAULT nextval('ui_kinds__id_seq'::regclass) NOT NULL,
	kind varchar(8) NOT NULL,
	description varchar(120) NULL,
	CONSTRAINT ui_kinds__kind_uix UNIQUE (kind),
	CONSTRAINT ui_kinds__pk PRIMARY KEY (id)
);

-- Permissions

ALTER TABLE canoa.ui_kinds OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.ui_kinds TO canoa_power;


-- canoa.ui_locales definition

-- Drop table

-- DROP TABLE canoa.ui_locales;

CREATE TABLE canoa.ui_locales (
	id int4 DEFAULT nextval('ui_locales__id_seq'::regclass) NOT NULL,
	locale varchar(8) NOT NULL,
	CONSTRAINT ui_locales__pk PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ui_locales__locale_uix ON canoa.ui_locales USING btree (locale);

-- Permissions

ALTER TABLE canoa.ui_locales OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.ui_locales TO canoa_power;
GRANT SELECT ON TABLE canoa.ui_locales TO canoa_connstr;


-- canoa.ui_sections definition

-- Drop table

-- DROP TABLE canoa.ui_sections;

CREATE TABLE canoa.ui_sections (
	id int4 DEFAULT nextval('ui_sections__id_seq'::regclass) NOT NULL,
	id_locale int4 NOT NULL,
	id_kind int4 DEFAULT 1 NOT NULL,
	"name" varchar(100) NOT NULL,
	title varchar(100) NOT NULL,
	name_lower varchar(100) GENERATED ALWAYS AS (lower(name::text)) STORED NULL,
	CONSTRAINT ui_sections__pk PRIMARY KEY (id),
	CONSTRAINT ui_sections__kind_fk FOREIGN KEY (id_kind) REFERENCES canoa.ui_kinds(id),
	CONSTRAINT ui_sections__locale_fk FOREIGN KEY (id_locale) REFERENCES canoa.ui_locales(id)
);
CREATE INDEX ui_sections__id_et_al_idx ON canoa.ui_sections USING btree (id) INCLUDE (id_locale, id_kind, name, title);
CREATE UNIQUE INDEX ui_sections__locale_name_lower_uix ON canoa.ui_sections USING btree (id_locale, name_lower);
CREATE UNIQUE INDEX ui_sections__locale_name_uix ON canoa.ui_sections USING btree (id_locale, name);

-- Permissions

ALTER TABLE canoa.ui_sections OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.ui_sections TO canoa_power;
GRANT SELECT ON TABLE canoa.ui_sections TO canoa_connstr;


-- canoa.ui_items definition

-- Drop table

-- DROP TABLE canoa.ui_items;

CREATE TABLE canoa.ui_items (
	id int4 DEFAULT nextval('ui_items__id_seq'::regclass) NOT NULL,
	id_section int4 NOT NULL,
	"name" varchar(100) NOT NULL,
	"text" text NOT NULL,
	description varchar(100) NULL,
	name_lower varchar(100) GENERATED ALWAYS AS (lower(name::text)) STORED NULL,
	CONSTRAINT ui_items__pk PRIMARY KEY (id),
	CONSTRAINT ui_items__section_name_lower_uix UNIQUE (id_section, name_lower),
	CONSTRAINT ui_items__section_name_uix UNIQUE (id_section, name),
	CONSTRAINT ui_items__id_sections_fk FOREIGN KEY (id_section) REFERENCES canoa.ui_sections(id)
);

-- Permissions

ALTER TABLE canoa.ui_items OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.ui_items TO canoa_power;
GRANT SELECT ON TABLE canoa.ui_items TO canoa_connstr;


-- canoa.log_user_sep definition

-- Drop table

-- DROP TABLE canoa.log_user_sep;

CREATE TABLE canoa.log_user_sep (
	id int4 DEFAULT nextval('log_user_sep__id_seq'::regclass) NOT NULL,
	id_sep int4 NOT NULL,
	id_users int4 NULL, -- Set NULL when remove sep from user (=id_users_prior)
	id_users_prior int4 NULL, -- The user ID of the previous owner of the SEP, or None if none was assigned
	done_at timestamp DEFAULT now() NOT NULL,
	done_by int4 NOT NULL, -- The new  SEP owner user id
	batch_code varchar(10) NOT NULL, -- (days since 2024.11.01).(ms) both in base duovigesimal (22)
	email_at timestamp NULL,
	email_error varchar(800) NULL,
	operation bpchar(1) NULL, -- (S)et, (R)emoved | (I)nserted (E)dited, marked as (D)eleted | schema (C)hanged,
	CONSTRAINT log_user_sep__pk PRIMARY KEY (id)
);
CREATE UNIQUE INDEX log_user_sep__batch_sep_oper__udx ON canoa.log_user_sep USING btree (batch_code, id_sep, operation);
COMMENT ON TABLE canoa.log_user_sep IS 'Action:
  » S & R is set in vw_mgmt_seps_user__on_upd
  » else see .models.private.py:Sep';

-- Column comments

COMMENT ON COLUMN canoa.log_user_sep.id_users IS 'Set NULL when remove sep from user (=id_users_prior)';
COMMENT ON COLUMN canoa.log_user_sep.id_users_prior IS 'The user ID of the previous owner of the SEP, or None if none was assigned';
COMMENT ON COLUMN canoa.log_user_sep.done_by IS 'The new  SEP owner user id';
COMMENT ON COLUMN canoa.log_user_sep.batch_code IS '(days since 2024.11.01).(ms) both in base duovigesimal (22)';
COMMENT ON COLUMN canoa.log_user_sep.operation IS '(S)et, (R)emoved | (I)nserted (E)dited, marked as (D)eleted | schema (C)hanged,';

-- Permissions

ALTER TABLE canoa.log_user_sep OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.log_user_sep TO canoa_power;
GRANT UPDATE, SELECT, INSERT ON TABLE canoa.log_user_sep TO canoa_connstr;


-- canoa."schema" definition

-- Drop table

-- DROP TABLE canoa."schema";

CREATE TABLE canoa."schema" (
	id int4 DEFAULT nextval('schema_id__seq'::regclass) NOT NULL,
	"name" varchar(100) NOT NULL,
	color bpchar(9) NULL, -- #rrbbgg
	title varchar(140) NOT NULL,
	description varchar(140) NULL,
	"content" text NULL,
	visible bool DEFAULT false NULL,
	name_lower varchar(100) GENERATED ALWAYS AS (lower(name::text)) STORED NULL,
	ins_at timestamp DEFAULT now() NULL,
	ins_by int4 NOT NULL,
	edt_at timestamp NULL,
	edt_by int4 NULL,
	del_at timestamp NULL,
	del_by int4 NULL,
	ui_order int4 NULL, -- Defines the display order of the elements UI.
	CONSTRAINT schema__pk PRIMARY KEY (id)
);
CREATE UNIQUE INDEX schema__name_lower_uix ON canoa.schema USING btree (name_lower);
CREATE UNIQUE INDEX schema__name_uix ON canoa.schema USING btree (name);
CREATE INDEX schema__ui_order__name_lower_idx ON canoa.schema USING btree (ui_order, name_lower);

-- Column comments

COMMENT ON COLUMN canoa."schema".color IS '#rrbbgg';
COMMENT ON COLUMN canoa."schema".ui_order IS 'Defines the display order of the elements UI.';

-- Permissions

ALTER TABLE canoa."schema" OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa."schema" TO canoa_power;
GRANT UPDATE, SELECT, INSERT ON TABLE canoa."schema" TO canoa_connstr;


-- canoa.sep definition

-- Drop table

-- DROP TABLE canoa.sep;

CREATE TABLE canoa.sep (
	id int4 DEFAULT nextval('sep_id__seq'::regclass) NOT NULL,
	"name" varchar(100) NOT NULL, -- ins by vw_mgmt_user_sep
	description varchar(140) NOT NULL, -- set by do_sep_edit
	visible bool DEFAULT false NULL,
	ins_at timestamp DEFAULT now() NULL, -- set by do_sep_edit |  vw_mgmt_user_sep
	name_lower varchar(100) GENERATED ALWAYS AS (lower(name::text)) STORED NULL,
	ins_by int4 NOT NULL, -- set by do_sep_edit | vw_mgmt_user_sep, see log
	icon_file_name varchar(120) NULL, -- set by do_sep_edit
	icon_svg text NULL, -- set by do_sep_edit
	id_schema int4 NOT NULL, -- set by do_sep_edit
	icon_original_name varchar(120) NULL, -- set by do_sep_edit
	icon_uploaded_at timestamp NULL, -- set by do_sep_edit
	icon_version int4 DEFAULT 0 NULL, -- set by do_sep_edit
	mgmt_users_id int4 NULL, -- Manager's id (set vw_mgmt_seps_user__on_upd)
	mgmt_users_at timestamp NULL -- Manager assigned datatime (vw_mgmt_seps_user__on_upd),
	mgmt_batch_code varchar(10) NULL, -- Atribution bacth code (see log_user_sep, vw_mgmt_seps_user__on_upd)
	icon_crc int8 NULL, -- set by do_sep_edit
	edt_by int4 NULL, -- set by do_sep_edit, user who did the last edition, see log
	edt_at timestamp NULL, -- set by do_sep_edit, when the last edition happened, see log
	del_by int4 NULL,
	del_at timestamp NULL,
	ico_by int4 NULL,
	ico_at timestamp NULL,
	ui_order int4 NULL, -- Defines the display order of the elements UI.
	id_spd int4 NULL, -- Reference for the SPatial Data File for the SEP
	CONSTRAINT sep__pk PRIMARY KEY (id),
	CONSTRAINT sep__scm__name__uix UNIQUE (id_schema, name),
	CONSTRAINT sep__scm__name_lower__uix UNIQUE (id_schema, name_lower)
);
CREATE INDEX sep__icon_crc__idx ON canoa.sep USING btree (icon_crc);
CREATE INDEX sep__id_schema__ui_order_idx ON canoa.sep USING btree (id_schema, ui_order);
CREATE INDEX sep__mgmt_users_id__idx ON canoa.sep USING btree (mgmt_users_id);

-- Column comments

COMMENT ON COLUMN canoa.sep."name" IS 'ins by vw_mgmt_user_sep';
COMMENT ON COLUMN canoa.sep.description IS 'set by do_sep_edit';
COMMENT ON COLUMN canoa.sep.ins_at IS 'set by do_sep_edit |  vw_mgmt_user_sep';
COMMENT ON COLUMN canoa.sep.ins_by IS 'set by do_sep_edit | vw_mgmt_user_sep, see log';
COMMENT ON COLUMN canoa.sep.icon_file_name IS 'set by do_sep_edit';
COMMENT ON COLUMN canoa.sep.icon_svg IS 'set by do_sep_edit';
COMMENT ON COLUMN canoa.sep.id_schema IS 'set by do_sep_edit';
COMMENT ON COLUMN canoa.sep.icon_original_name IS 'set by do_sep_edit';
COMMENT ON COLUMN canoa.sep.icon_uploaded_at IS 'set by do_sep_edit';
COMMENT ON COLUMN canoa.sep.icon_version IS 'set by do_sep_edit';
COMMENT ON COLUMN canoa.sep.mgmt_users_id IS 'Manager''s id (set vw_mgmt_seps_user__on_upd)';
COMMENT ON COLUMN canoa.sep.mgmt_users_at IS 'Manager assigned datatime (vw_mgmt_seps_user__on_upd)';
COMMENT ON COLUMN canoa.sep.mgmt_batch_code IS 'Atribution bacth code (see log_user_sep, vw_mgmt_seps_user__on_upd)';
COMMENT ON COLUMN canoa.sep.icon_crc IS 'set by do_sep_edit';
COMMENT ON COLUMN canoa.sep.edt_by IS 'set by do_sep_edit, user who did the last edition, see log';
COMMENT ON COLUMN canoa.sep.edt_at IS 'set by do_sep_edit, when the last edition happened, see log';
COMMENT ON COLUMN canoa.sep.ui_order IS 'Defines the display order of the elements UI.';
COMMENT ON COLUMN canoa.sep.id_spd IS 'Reference for the SPatial Data File for the SEP';

-- Permissions

ALTER TABLE canoa.sep OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.sep TO canoa_power;
GRANT UPDATE, SELECT, INSERT ON TABLE canoa.sep TO canoa_connstr;


-- canoa.spatial_data_files definition

-- Drop table

-- DROP TABLE canoa.spatial_data_files;

CREATE TABLE canoa.spatial_data_files (
	id int4 DEFAULT nextval('spatial_data_files_id__seq'::regclass) NOT NULL,
	spd_name varchar(60) NOT NULL,
	spd_name_lower varchar(60) GENERATED ALWAYS AS (lower(spd_name::text)) STORED NOT NULL,
	spd_title varchar(80) NOT NULL,
	spd_description varchar(120) NULL,
	layer_name varchar(60) NULL,
	layer_crs varchar(12) NULL, -- Coordinate Reference System
	layer_health float4 NULL, -- Layer health score 0-100 %
	features_count int4 NULL,
	field_id varchar(12) NULL, -- Spatial Data ID
	field_name varchar(12) NULL, -- Name field/attribute
	field_alt_name varchar(12) NULL, -- Secondary Name field/attribute
	original_file_name varchar(140) NOT NULL,
	file_name varchar(140) NOT NULL,
	file_size int4 NOT NULL,
	file_crc32 int8 NOT NULL,
	registered_at timestamp NOT NULL,
	registered_by int4 NOT NULL,
	edited_at timestamp NULL,
	edited_by int4 NULL,
	file_data text NULL,
	CONSTRAINT spatial_data_files__name_lower_uix UNIQUE (spd_name_lower),
	CONSTRAINT spatial_data_files__pk PRIMARY KEY (id)
);

-- Column comments

COMMENT ON COLUMN canoa.spatial_data_files.layer_crs IS 'Coordinate Reference System';
COMMENT ON COLUMN canoa.spatial_data_files.layer_health IS 'Layer health score 0-100 %';
COMMENT ON COLUMN canoa.spatial_data_files.field_id IS 'Spatial Data ID';
COMMENT ON COLUMN canoa.spatial_data_files.field_name IS 'Name field/attribute';
COMMENT ON COLUMN canoa.spatial_data_files.field_alt_name IS 'Secondary Name field/attribute';

-- Permissions

ALTER TABLE canoa.spatial_data_files OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.spatial_data_files TO canoa_power;
GRANT UPDATE, SELECT, INSERT ON TABLE canoa.spatial_data_files TO canoa_connstr;


-- canoa.user_data_files definition

-- Drop table

-- DROP TABLE canoa.user_data_files;

CREATE TABLE canoa.user_data_files (
	id int4 DEFAULT nextval('user_data_files__id_seq'::regclass) NOT NULL,
	id_users int4 NOT NULL, -- Foreign key of the user responsible for starting the validation process.
	file_name varchar(140) NOT NULL, -- Stores the name of the received file (uploaded or downloaded) with illegal characters removed (eg /)
	file_size int4 NOT NULL,
	file_crc32 int8 NOT NULL,
	ticket varchar(40) NOT NULL, -- Unique Key:  user_code:5 _ date:10 _ msOfDay(base 22): 10¶12345_YYYY-MM-DD_123456789A
	registered_at timestamp NOT NULL, -- set on trigger
	email_sent bool DEFAULT false NOT NULL,
	email_sent_at timestamp NULL, -- set on trigger
	ticket_lower varchar(40) GENERATED ALWAYS AS (lower(ticket::text)) STORED NULL, -- A calculated column derived from the ticket column, taht stores the lowercase version of the ticket value to ensure unique case-insensitive index.
	error_code int4 NULL,
	error_msg varchar(512) NULL,
	error_at timestamp NULL, -- set on trigger
	error_handled varchar NULL, -- If not NULL, indicates whether an error has been reviewed and addressed by the administrator. "Handled" can include actions such as fixing the error, contacting the user, or updating the validator.
	upload_start_at timestamp NULL, -- obsolete
	report_ready_at timestamp NULL, -- obsolete -> g_report_ready_at
	error_text text NULL, -- data_validator std_err
	success_text text NULL, -- data_validator std_out
	user_receipt varchar(15) NULL, -- User Receipt Code= YYYY-MM_DD_crc16(ticket)(4)
	from_os varchar(1) NULL, -- Indicates the operating system used to run the app, with 'W' for Windows and 'L' for Linux.
	original_name varchar(80) NULL, -- Stores the original name of the received file (eg invalid chars are removed).
	b_process_started_at timestamp NULL,
	a_received_at timestamp NULL,
	c_check_started_at timestamp NULL,
	d_register_started_at timestamp NULL,
	e_unzip_started_at timestamp NULL,
	f_submit_started_at timestamp NULL,
	g_email_started_at timestamp NULL, -- obsolete -> h_email_started_at
	z_process_end_at timestamp NULL,
	file_origin varchar(1) NULL, -- Indicates the source of the uploaded file, with 'L' for local uploads and 'C' for cloud downloads.
	app_version varchar(12) NULL, -- Stores the version number of Canoa at the time of validation.
	process_version varchar(12) NULL, -- Stores the version number of Canoa's 'validate_process' at the time of validation.
	id_sep int4 NULL -- The SEP ID attributed to the user at the time of validation.,
	report_errors int4 NULL, -- Extracted standard output.
	report_warns int4 NULL, -- Extracted standard output.
	report_tests int4 NULL, -- Extracted standard output.
	validator_version varchar(16) NULL, -- Stores the version number of the app used for validation, extracted standard output.
	db_version varchar(12) NULL, -- Stores the version number of the database schema applied at the time of validation. This value is set by the trigger based on the latest version recorded in the db_version table.
	exit_code int4 DEFAULT 0 NULL, -- Exit code of data_validate
	validator_result varchar(1024) NULL, -- A json str extracted from the standard output or, if not found, created by Canoa.
	g_report_ready_at timestamp NULL,
	h_email_started_at timestamp NULL,
	log_file_name varchar(200) NULL, -- User log file name, use for debugging purposes.
	id_spd int4 NULL, -- The SPD ID assigned to the selected SEP at the time of validation.
	CONSTRAINT user_data_files__pk PRIMARY KEY (id),
	CONSTRAINT user_data_files__ticket_lower_uix UNIQUE (ticket_lower)
);
CREATE INDEX user_data_files__id_sep__report_errors__ix ON canoa.user_data_files USING btree (id_sep, report_errors DESC);
COMMENT ON INDEX canoa.user_data_files__id_sep__report_errors__ix IS 'for vw_export_data_files';
CREATE INDEX user_data_files__id_users__registered_ix ON canoa.user_data_files USING btree (id_users, registered_at DESC);
COMMENT ON INDEX canoa.user_data_files__id_users__registered_ix IS 'for vw_user_data_files';
CREATE INDEX user_data_files__id_users_ix ON canoa.user_data_files USING btree (id_users);

-- Column comments

COMMENT ON COLUMN canoa.user_data_files.id_users IS 'Foreign key of the user responsible for starting the validation process.';
COMMENT ON COLUMN canoa.user_data_files.file_name IS 'Stores the name of the received file (uploaded or downloaded) with illegal characters removed (eg /)';
COMMENT ON COLUMN canoa.user_data_files.ticket IS 'Unique Key:  user_code:5 _ date:10 _ msOfDay(base 22): 10
12345_YYYY-MM-DD_123456789A';
COMMENT ON COLUMN canoa.user_data_files.registered_at IS 'set on trigger';
COMMENT ON COLUMN canoa.user_data_files.email_sent_at IS 'set on trigger';
COMMENT ON COLUMN canoa.user_data_files.ticket_lower IS 'A calculated column derived from the ticket column, taht stores the lowercase version of the ticket value to ensure unique case-insensitive index.';
COMMENT ON COLUMN canoa.user_data_files.error_at IS 'set on trigger';
COMMENT ON COLUMN canoa.user_data_files.error_handled IS 'If not NULL, indicates whether an error has been reviewed and addressed by the administrator. "Handled" can include actions such as fixing the error, contacting the user, or updating the validator.';
COMMENT ON COLUMN canoa.user_data_files.upload_start_at IS 'obsolete';
COMMENT ON COLUMN canoa.user_data_files.report_ready_at IS 'obsolete -> g_report_ready_at';
COMMENT ON COLUMN canoa.user_data_files.error_text IS 'data_validator std_err';
COMMENT ON COLUMN canoa.user_data_files.success_text IS 'data_validator std_out';
COMMENT ON COLUMN canoa.user_data_files.user_receipt IS 'User Receipt Code= YYYY-MM_DD_crc16(ticket)(4)';
COMMENT ON COLUMN canoa.user_data_files.from_os IS 'Indicates the operating system used to run the app, with ''W'' for Windows and ''L'' for Linux.';
COMMENT ON COLUMN canoa.user_data_files.original_name IS 'Stores the original name of the received file (eg invalid chars are removed).';
COMMENT ON COLUMN canoa.user_data_files.g_email_started_at IS 'obsolete -> h_email_started_at';
COMMENT ON COLUMN canoa.user_data_files.file_origin IS 'Indicates the source of the uploaded file, with ''L'' for local uploads and ''C'' for cloud downloads.';
COMMENT ON COLUMN canoa.user_data_files.app_version IS 'Stores the version number of Canoa at the time of validation.';
COMMENT ON COLUMN canoa.user_data_files.process_version IS 'Stores the version number of Canoa''s ''validate_process'' at the time of validation.';
COMMENT ON COLUMN canoa.user_data_files.id_sep IS 'The SEP ID attributed to the user at the time of validation.';
COMMENT ON COLUMN canoa.user_data_files.report_errors IS 'Extracted standard output.';
COMMENT ON COLUMN canoa.user_data_files.report_warns IS 'Extracted standard output.';
COMMENT ON COLUMN canoa.user_data_files.report_tests IS 'Extracted standard output.';
COMMENT ON COLUMN canoa.user_data_files.validator_version IS 'Stores the version number of the app used for validation, extracted standard output.';
COMMENT ON COLUMN canoa.user_data_files.db_version IS 'Stores the version number of the database schema applied at the time of validation. This value is set by the trigger based on the latest version recorded in the db_version table.';
COMMENT ON COLUMN canoa.user_data_files.exit_code IS 'Exit code of data_validate';
COMMENT ON COLUMN canoa.user_data_files.validator_result IS 'A json str extracted from the standard output or, if not found, created by Canoa.';
COMMENT ON COLUMN canoa.user_data_files.log_file_name IS 'User log file name, use for debugging purposes.';
COMMENT ON COLUMN canoa.user_data_files.id_spd IS 'The SPD ID assigned to the selected SEP at the time of validation.';

-- Table Triggers

create trigger user_data_files__on_ins_upd before
insert
    or
update
    on
    canoa.user_data_files for each row execute function user_data_files__on_ins_upd();

-- Permissions

ALTER TABLE canoa.user_data_files OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.user_data_files TO canoa_power;
GRANT UPDATE, SELECT, INSERT ON TABLE canoa.user_data_files TO canoa_connstr;


-- canoa.users definition

-- Drop table

-- DROP TABLE canoa.users;

CREATE TABLE canoa.users (
	id int4 DEFAULT nextval('users__id_seq'::regclass) NOT NULL,
	id_role int4 NOT NULL,
	username varchar(100) NOT NULL,
	email varchar(100) NOT NULL, -- always lower case (see trigger)
	"password" bytea NOT NULL,
	recover_email_token varchar(100) NULL, -- It should be renamed to "recover_pw_token"
	recover_email_token_at timestamp NULL, -- It should be renamed to "recover_pw_token_at"
	registered_at timestamp DEFAULT now() NULL,
	email_verified_at timestamp NULL, -- Date and time when the email validation process was completed.
	password_changed_at timestamp NULL,
	disabled bool DEFAULT false NOT NULL, -- Ther user has been disabled, don't allow to interact
	disabled_at timestamp NULL,
	email_verified bool GENERATED ALWAYS AS (email_verified_at IS NOT NULL) STORED NOT NULL, -- Generated column
	username_lower varchar(100) GENERATED ALWAYS AS (lower(username::text)) STORED NULL,
	last_login_at timestamp NULL,
	mgmt_sep_id int4 NULL,
	mgmt_sep_at timestamp NULL,
	email_changed_at timestamp NULL,
	mgmt_batch_code varchar(10) NULL,
	password_failures int4 DEFAULT 0 NULL,
	password_failed_at timestamp NULL,
	lang varchar(8) DEFAULT 'pt-BR'::character varying NOT NULL, -- HTML attribute & DB filter
	debug bool DEFAULT false NOT NULL, -- If true, the app will run in debugging mode for this user
	verify_email_token varchar(8) NULL, -- Token created and sent during the email address verification process
	verify_email_sent_at timestamp NULL, -- Updated upon starting the email address verification process
	last_logout_at timestamp NULL,
	CONSTRAINT users__email_uix UNIQUE (email),
	CONSTRAINT users__mgmt_sep_uix UNIQUE (mgmt_sep_id),
	CONSTRAINT users__pk PRIMARY KEY (id),
	CONSTRAINT users__username_lower_uix UNIQUE (username_lower),
	CONSTRAINT users__username_uix UNIQUE (username)
);
CREATE UNIQUE INDEX users__recover_email_token_idx ON canoa.users USING btree (recover_email_token);

-- Column comments

COMMENT ON COLUMN canoa.users.email IS 'always lower case (see trigger)';
COMMENT ON COLUMN canoa.users.recover_email_token IS 'It should be renamed to "recover_pw_token"';
COMMENT ON COLUMN canoa.users.recover_email_token_at IS 'It should be renamed to "recover_pw_token_at"';
COMMENT ON COLUMN canoa.users.email_verified_at IS 'Date and time when the email validation process was completed.';
COMMENT ON COLUMN canoa.users.disabled IS 'Ther user has been disabled, don''t allow to interact';
COMMENT ON COLUMN canoa.users.email_verified IS 'Generated column';
COMMENT ON COLUMN canoa.users.lang IS 'HTML attribute & DB filter';
COMMENT ON COLUMN canoa.users.debug IS 'If true, the app will run in debugging mode for this user';
COMMENT ON COLUMN canoa.users.verify_email_token IS 'Token created and sent during the email address verification process';
COMMENT ON COLUMN canoa.users.verify_email_sent_at IS 'Updated upon starting the email address verification process';

-- Table Triggers

create trigger users_ins_upd before
insert
    or
update
    on
    canoa.users for each row execute function users__on_ins_upd();

-- Permissions

ALTER TABLE canoa.users OWNER TO canoa_power;
GRANT REFERENCES, UPDATE, SELECT, INSERT, DELETE, TRIGGER, TRUNCATE ON TABLE canoa.users TO canoa_power;
GRANT UPDATE, SELECT, INSERT ON TABLE canoa.users TO canoa_connstr;


-- canoa.log_user_sep foreign keys

ALTER TABLE canoa.log_user_sep ADD CONSTRAINT log_user_sep__done_by_fk FOREIGN KEY (done_by) REFERENCES canoa.users(id);
ALTER TABLE canoa.log_user_sep ADD CONSTRAINT log_user_sep__sep_fk FOREIGN KEY (id_sep) REFERENCES canoa.sep(id);
ALTER TABLE canoa.log_user_sep ADD CONSTRAINT log_user_sep__users_fk FOREIGN KEY (id_users) REFERENCES canoa.users(id);
ALTER TABLE canoa.log_user_sep ADD CONSTRAINT log_user_sep__users_prior_fk FOREIGN KEY (id_users_prior) REFERENCES canoa.users(id);


-- canoa."schema" foreign keys

ALTER TABLE canoa."schema" ADD CONSTRAINT schema__del_by___users_fk FOREIGN KEY (del_by) REFERENCES canoa.users(id);
ALTER TABLE canoa."schema" ADD CONSTRAINT schema__edt_by___users_fk FOREIGN KEY (edt_by) REFERENCES canoa.users(id);
ALTER TABLE canoa."schema" ADD CONSTRAINT schema__ins_by___users_fk FOREIGN KEY (ins_by) REFERENCES canoa.users(id);


-- canoa.sep foreign keys

ALTER TABLE canoa.sep ADD CONSTRAINT sep__del_by___users_fk FOREIGN KEY (del_by) REFERENCES canoa.users(id);
ALTER TABLE canoa.sep ADD CONSTRAINT sep__edt_by___users_fk FOREIGN KEY (edt_by) REFERENCES canoa.users(id);
ALTER TABLE canoa.sep ADD CONSTRAINT sep__ico_by___users_fk FOREIGN KEY (ico_by) REFERENCES canoa.users(id);
ALTER TABLE canoa.sep ADD CONSTRAINT sep__ins_by___users_fk FOREIGN KEY (ins_by) REFERENCES canoa.users(id);
ALTER TABLE canoa.sep ADD CONSTRAINT sep__schema_fk FOREIGN KEY (id_schema) REFERENCES canoa."schema"(id);
ALTER TABLE canoa.sep ADD CONSTRAINT sep__spatial_data_files_fk FOREIGN KEY (id_spd) REFERENCES canoa.spatial_data_files(id);
ALTER TABLE canoa.sep ADD CONSTRAINT sep__users_fk FOREIGN KEY (mgmt_users_id) REFERENCES canoa.users(id);


-- canoa.spatial_data_files foreign keys

ALTER TABLE canoa.spatial_data_files ADD CONSTRAINT spatial_data_files__users_edt FOREIGN KEY (edited_by) REFERENCES canoa.users(id);
ALTER TABLE canoa.spatial_data_files ADD CONSTRAINT spatial_data_files__users_ins FOREIGN KEY (registered_by) REFERENCES canoa.users(id);


-- canoa.user_data_files foreign keys

ALTER TABLE canoa.user_data_files ADD CONSTRAINT user_data_files__sep_fk FOREIGN KEY (id_sep) REFERENCES canoa.sep(id);
ALTER TABLE canoa.user_data_files ADD CONSTRAINT user_data_files__users_fk FOREIGN KEY (id_users) REFERENCES canoa.users(id);


-- canoa.users foreign keys

ALTER TABLE canoa.users ADD CONSTRAINT users__role_id_fk FOREIGN KEY (id_role) REFERENCES canoa.roles(id);
ALTER TABLE canoa.users ADD CONSTRAINT users__sep_id_fk FOREIGN KEY (mgmt_sep_id) REFERENCES canoa.sep(id);


-- canoa.vw_export_data_files source

CREATE OR REPLACE VIEW canoa.vw_export_data_files
AS SELECT id,
    user_id,
    sep_id,
    scm_id,
    file_origin,
    file_name,
    sep_fullname,
    uploaded,
    report_errors
   FROM ( SELECT udf.id,
            udf.id_users AS user_id,
            sep.sep_id,
            sep.scm_id,
            sep.is_visible,
            sep.sep_fullname,
            udf.file_origin,
            udf.stored_file_name AS file_name,
            udf.registered_at AS uploaded,
            udf.report_warns,
            udf.report_errors,
            row_number() OVER (PARTITION BY udf.id_sep ORDER BY udf.registered_at DESC) AS rn_recent,
            row_number() OVER (PARTITION BY udf.id_sep ORDER BY udf.report_errors) AS rn_lowest_errors
           FROM vw_user_data_files udf
             JOIN vw_scm_sep sep ON udf.id_sep = sep.sep_id
          WHERE udf.id_sep IS NOT NULL AND sep.is_visible) udf_last_file
  WHERE rn_recent = 1
  ORDER BY (COALESCE(report_errors, '-1'::integer)) DESC;

-- Permissions

ALTER TABLE canoa.vw_export_data_files OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_export_data_files TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_export_data_files TO canoa_connstr;


-- canoa.vw_log_user_sep source

CREATE OR REPLACE VIEW canoa.vw_log_user_sep
AS SELECT log.id,
    log.id_sep,
    sep.sep_fullname,
    log.id_users AS curr_user_id,
    u.username AS curr_user_name,
    log.id_users_prior AS prior_user_id,
    up.username AS prior_user_name,
    log.done_at,
    log.done_by,
    ub.username AS done_by_name,
    log.batch_code,
    log.operation,
    log.email_at,
    log.email_error
   FROM log_user_sep log
     LEFT JOIN vw_scm_sep sep ON sep.sep_id = log.id_sep
     LEFT JOIN users u ON u.id = log.id_users
     LEFT JOIN users up ON up.id = log.id_users_prior
     LEFT JOIN users ub ON ub.id = log.done_by
  ORDER BY log.id_sep, log.done_at DESC;

COMMENT ON VIEW canoa.vw_log_user_sep IS 'Read-only audit-log grid for log_user_sep: resolves id_sep/id_users/id_users_prior/done_by to names for display. See carranca/models/private/log_user_sep_grid.py. `operation`s single-char code is decoded to a label in Python, not here.';

-- Permissions

ALTER TABLE canoa.vw_log_user_sep OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_log_user_sep TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_log_user_sep TO canoa_connstr;


-- canoa.vw_mgmt_email_sep source

CREATE OR REPLACE VIEW canoa.vw_mgmt_email_sep
AS SELECT id,
    ( SELECT users.username
           FROM users
          WHERE users.id = log.id_users) AS new_user_name,
    ( SELECT users.email
           FROM users
          WHERE users.id = log.id_users) AS new_user_email,
    ( SELECT users.username
           FROM users
          WHERE users.id = log.id_users_prior) AS old_user_name,
    ( SELECT users.email
           FROM users
          WHERE users.id = log.id_users_prior) AS old_user_email,
    ( SELECT vw.sep_fullname
           FROM vw_scm_sep vw
          WHERE vw.sep_id = log.id_sep) AS sep_fullname,
    email_at,
    email_error,
    batch_code
   FROM log_user_sep log;

COMMENT ON VIEW canoa.vw_mgmt_email_sep IS '*Updatable View* that exposes columns to assist in sending emails to users when the SEP assigned to them is changed by an admin.';

-- Permissions

ALTER TABLE canoa.vw_mgmt_email_sep OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_mgmt_email_sep TO canoa_power;
GRANT UPDATE, SELECT, INSERT ON TABLE canoa.vw_mgmt_email_sep TO canoa_connstr;


-- canoa.vw_mgmt_seps_user source

CREATE OR REPLACE VIEW canoa.vw_mgmt_seps_user
AS SELECT sep.id,
    sep.name,
    ((scm.name::text || '/'::character(1)::text))::character varying(100)::text || sep.name::text AS fullname,
    lower((scm.name::text || '/'::character(1)::text) || sep.name::text) AS fullname_lower,
    sep.icon_file_name,
    sep.description,
    sep.visible,
    sdf.id AS spd_id,
    sdf.spd_name,
    scm.id AS scm_id,
    scm.name AS scm_name,
    usr.id AS user_id,
    usr.disabled AS user_disabled,
    usr.username AS user_curr,
    ' '::character varying(100) AS user_new,
    sep.mgmt_users_at AS assigned_at,
    0 AS assigned_by,
    ' '::character varying(10) AS batch_code
   FROM sep sep
     JOIN vw_schema scm ON sep.id_schema = scm.id
     LEFT JOIN users usr ON usr.id = sep.mgmt_users_id
     LEFT JOIN spatial_data_files sdf ON sdf.id = sep.id_spd
  ORDER BY (lower((scm.name::text || '/'::character(1)::text) || sep.name::text));

-- View Triggers

create trigger vw_mgmt_users_sep__upd instead of
update
    on
    canoa.vw_mgmt_seps_user for each row execute function vw_mgmt_seps_user__on_upd();

-- Permissions

ALTER TABLE canoa.vw_mgmt_seps_user OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_mgmt_seps_user TO canoa_power;
GRANT UPDATE, SELECT, INSERT ON TABLE canoa.vw_mgmt_seps_user TO canoa_connstr;


-- canoa.vw_mgmt_user_sep source

CREATE OR REPLACE VIEW canoa.vw_mgmt_user_sep
AS SELECT usr.id AS user_id,
    scmsep.sep_id,
    usr.username AS user_name,
    usr.disabled AS user_disabled,
    scmsep.sep_fullname AS scm_sep_curr,
    ' '::character varying(201) AS scm_sep_new,
    usr.mgmt_sep_at AS assigned_at,
    0 AS assigned_by,
    ' '::character varying(10) AS batch_code
   FROM users usr
     JOIN roles rol ON usr.id_role = rol.id
     LEFT JOIN vw_scm_sep scmsep ON scmsep.sep_id = usr.mgmt_sep_id
  WHERE rol.abbr::text = 'SEP'::text
  ORDER BY usr.username_lower;

COMMENT ON VIEW canoa.vw_mgmt_user_sep IS 'OBSOLETE';

-- View Triggers

create trigger vw_mgmt_user_sep__upd instead of
update
    on
    canoa.vw_mgmt_user_sep for each row execute function vw_mgmt_user_sep__on_upd();

-- Permissions

ALTER TABLE canoa.vw_mgmt_user_sep OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_mgmt_user_sep TO canoa_power;
GRANT UPDATE, SELECT ON TABLE canoa.vw_mgmt_user_sep TO canoa_connstr;


-- canoa.vw_schema source

CREATE OR REPLACE VIEW canoa.vw_schema
AS SELECT id,
    name,
    name_lower,
    title,
    description,
    color,
    visible
   FROM schema
  ORDER BY name;

-- Permissions

ALTER TABLE canoa.vw_schema OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_schema TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_schema TO canoa_connstr;


-- canoa.vw_schema_grid source

CREATE OR REPLACE VIEW canoa.vw_schema_grid
AS WITH sep_counts AS (
         SELECT sep.id_schema,
            count(*) AS sep_count,
            count(*) FILTER (WHERE sep.visible) AS v_sep_count
           FROM sep
          GROUP BY sep.id_schema
        )
 SELECT s.id,
    s.name,
    s.title,
    s.color,
    s.visible,
    COALESCE(sc.sep_count, 0::bigint) AS sep_count,
    COALESCE(sc.v_sep_count, 0::bigint) AS v_sep_count,
    (COALESCE(sc.v_sep_count, 0::bigint)::text || '/'::text) || COALESCE(sc.sep_count, 0::bigint)::text AS sep_v2t,
    s.name_lower,
    s.ui_order
   FROM schema s
     LEFT JOIN sep_counts sc ON sc.id_schema = s.id
  ORDER BY s.ui_order, s.name_lower;

COMMENT ON VIEW canoa.vw_schema_grid IS 'Used in scm_grid';
COMMENT ON COLUMN canoa.vw_schema_grid.v_sep_count IS 'Visible seps count';
COMMENT ON COLUMN canoa.vw_schema_grid.sep_v2t IS 'sep Visible to Total count';

-- Permissions

ALTER TABLE canoa.vw_schema_grid OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_schema_grid TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_schema_grid TO canoa_connstr;


-- canoa.vw_scm_sep source

CREATE OR REPLACE VIEW canoa.vw_scm_sep
AS SELECT sep.id AS sep_id,
    scm.id AS scm_id,
    scm.name AS schema,
    sep.name AS sep,
    sep.icon_file_name,
    ((scm.name::text || '/'::character varying(100)::text))::character varying(101)::text || sep.name::character varying(101)::text AS sep_fullname,
    lower(((scm.name::text || '/'::character varying(100)::text))::character varying(101)::text || sep.name::character varying(101)::text) AS sep_fullname_lower,
    sep.mgmt_users_id AS user_id,
    sep.visible AND scm.visible AS is_visible
   FROM sep sep
     JOIN vw_schema scm ON sep.id_schema = scm.id
  ORDER BY sep.mgmt_users_id, (lower(((scm.name::text || '/'::character varying(100)::text))::character varying(101)::text || sep.name::character varying(101)::text));

-- Permissions

ALTER TABLE canoa.vw_scm_sep OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_scm_sep TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_scm_sep TO canoa_connstr;


-- canoa.vw_ui_for_edit source

CREATE OR REPLACE VIEW canoa.vw_ui_for_edit
AS SELECT id,
    name,
    description,
    text,
    id_section AS sec_id,
    ( SELECT sec.name
           FROM ui_sections sec
          WHERE sec.id = itm.id_section) AS sec_name,
    ( SELECT sec.title
           FROM ui_sections sec
          WHERE sec.id = itm.id_section) AS sec_title,
    ( SELECT uit.locale
           FROM vw_ui_texts uit
          WHERE uit.id = itm.id) AS locale,
    ( SELECT uit.kind
           FROM vw_ui_texts uit
          WHERE uit.id = itm.id) AS kind
   FROM ui_items itm
  ORDER BY (( SELECT sec.name
           FROM ui_sections sec
          WHERE sec.id = itm.id_section)), name;

COMMENT ON VIEW canoa.vw_ui_for_edit IS 'Todo: Trigger for Update';

-- Permissions

ALTER TABLE canoa.vw_ui_for_edit OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_ui_for_edit TO canoa_power;
GRANT UPDATE, SELECT ON TABLE canoa.vw_ui_for_edit TO canoa_connstr;


-- canoa.vw_ui_texts source

CREATE OR REPLACE VIEW canoa.vw_ui_texts
AS SELECT itm.id,
    itm.name AS item,
    itm.text,
    sec.name AS section,
    itm.name_lower AS item_lower,
    sec.name_lower AS section_lower,
    sec.title,
    loc.locale,
    knd.kind
   FROM ui_items itm
     JOIN ui_sections sec ON sec.id = itm.id_section
     JOIN ui_locales loc ON loc.id = sec.id_locale
     JOIN ui_kinds knd ON knd.id = sec.id_kind
  ORDER BY loc.locale, sec.name_lower, itm.name_lower;

-- Permissions

ALTER TABLE canoa.vw_ui_texts OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_ui_texts TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_ui_texts TO canoa_connstr;


-- canoa.vw_user_data_files source

CREATE OR REPLACE VIEW canoa.vw_user_data_files
AS SELECT udf.id,
    udf.id_sep,
    udf.id_users,
    usr.username,
    usr.email,
    sep.sep_id,
    sep.sep_fullname,
    concat(TRIM(BOTH FROM udf.ticket), '_', TRIM(BOTH FROM udf.file_name))::character varying(180) AS stored_file_name,
        CASE
            WHEN udf.original_name IS NULL OR udf.original_name::text = ''::text THEN udf.file_name
            ELSE udf.original_name
        END AS original_name,
    udf.file_size,
    udf.file_crc32,
    udf.file_origin,
    udf.user_receipt,
    udf.report_errors,
    udf.report_warns,
    udf.registered_at
   FROM user_data_files udf
     JOIN users usr ON usr.id = udf.id_users
     LEFT JOIN vw_scm_sep sep ON udf.id_sep = sep.sep_id
  ORDER BY udf.id_users, udf.registered_at DESC;

COMMENT ON VIEW canoa.vw_user_data_files IS 'For received_files_mgmt.py';

-- Permissions

ALTER TABLE canoa.vw_user_data_files OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_user_data_files TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_user_data_files TO canoa_connstr;


-- canoa.vw_user_data_files_count source

CREATE OR REPLACE VIEW canoa.vw_user_data_files_count
AS SELECT usr.id,
    usr.username AS user_name,
    usr.email AS user_email,
    usr.id_role AS rol_id,
    rol.abbr AS rol_abbr,
    rol.name AS rol_name,
    count(udf.id) AS files_count
   FROM users usr
     LEFT JOIN user_data_files udf ON usr.id = udf.id_users
     LEFT JOIN roles rol ON usr.id_role = rol.id
  WHERE udf.error_text IS NULL OR udf.error_text = ''::text
  GROUP BY usr.id, usr.username, usr.id_role, usr.email, rol.abbr, rol.name
  ORDER BY usr.username;

COMMENT ON VIEW canoa.vw_user_data_files_count IS 'Used is carranca\private\received_files';

-- Permissions

ALTER TABLE canoa.vw_user_data_files_count OWNER TO canoa_power;
GRANT SELECT, DELETE ON TABLE canoa.vw_user_data_files_count TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_user_data_files_count TO canoa_connstr;



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
GRANT ALL ON FUNCTION canoa.ui_locales__on_ins_upd() TO public;
GRANT ALL ON FUNCTION canoa.ui_locales__on_ins_upd() TO canoa_power;

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

  
	return new;
end;
$function$
;

-- Permissions

ALTER FUNCTION canoa.user_data_files__on_ins_upd() OWNER TO canoa_power;
GRANT ALL ON FUNCTION canoa.user_data_files__on_ins_upd() TO public;
GRANT ALL ON FUNCTION canoa.user_data_files__on_ins_upd() TO canoa_power;

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

	-- -----------------------------------------------------------------------------------------
	-- /!\ Keep a copy of this file updated in carranca\database\functions\users__on_ins_upd.sql
    -- ------------------------------------------------------------------------------------------

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
		-- clean garbage from recover_email_token
		reset_recover_pw_token := true;
	end if;
	-- TODO check min length of recover_email_token

	-- not needed any more
	if reset_recover_pw_token then
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

    -- -------------------------------------------------------------------------------------------------
	-- /!\ Keep a copy of this file updated in carranca\database\functions\vw_mgmt_seps_user__on_upd.sql
    -- -------------------------------------------------------------------------------------------------

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

-- Permissions

ALTER FUNCTION canoa.vw_mgmt_seps_user__on_upd() OWNER TO canoa_power;
GRANT ALL ON FUNCTION canoa.vw_mgmt_seps_user__on_upd() TO canoa_power;

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

	-- ------------------------------------------------------------------------------------------------
	-- /!\ Keep a copy of this file updated in carranca\database\functions\vw_mgmt_user_sep__on_upd.sql
    -- ------------------------------------------------------------------------------------------------

	-- mgd 2024-10-25, 11-08
	sep_new = Null;
	dt_sec = now(); 
	if NEW.scm_sep_new is Null or trim(NEW.scm_sep_new) = '' then
		-- remove SEP from user
		id_sep_new := Null;
	else
		-- find sep's id for the new schem_name/sep_name 
		fullname := trim(NEW.scm_sep_new);
		select sep_id into id_sep_new from canoa.vw_scm_sep as vw where (vw.sep_fullname_lower = lower(fullname));

		if (id_sep_new is not Null) then
			select username into user_using_it from users where mgmt_sep_id = id_sep_new and not id = NEW.user_id;
			if user_using_it is not Null then
 				raise exception '[^|O SEP "%" está atualmente atribuído a %. Por favor, remova-o dele primeiro.|^]', fullname, user_using_it;
			end if;
		else -- if not found:
			-- add a new sep_name into table sep
			-- fullname = schem_name/sep_name => find the schema's id => schema_name = part[1]
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
$function$
;

-- Permissions

ALTER FUNCTION canoa.vw_mgmt_user_sep__on_upd() OWNER TO canoa_power;
GRANT ALL ON FUNCTION canoa.vw_mgmt_user_sep__on_upd() TO canoa_power;


-- Permissions

GRANT ALL ON SCHEMA canoa TO canoa_power;
GRANT USAGE ON SCHEMA canoa TO mauro;
GRANT USAGE ON SCHEMA canoa TO canoa_users;
ALTER DEFAULT PRIVILEGES FOR ROLE canoa_users IN SCHEMA canoa GRANT UPDATE, SELECT, INSERT, DELETE ON TABLES TO canoa_users;