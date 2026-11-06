-- update_canoa.sql
-- Pending DB changes, to apply first on canoa_dev, then on canoa (production).
--
-- Schema-independent: no `canoa.` prefixes. Set the target schema ONCE below;
-- unqualified names in the views are bound to it at creation time.
-- Run the whole script (DBeaver: Alt+X), not statement by statement.
-- Idempotent: it can run again on a DB that already has (part of) it.
--
-- Equipe da Canoa -- 2026
-- mgd 2026-10-24

set search_path to canoa_dev;  -- ⚠️ canoa_dev for testing, canoa for production

begin;

-- ============================================================================
-- 2026-11-05 `validated` column -- Refs #61
-- A failed (re)validation must not replace the last good file of a SEP.
-- user_data_files gets `validated` (set by submit.py), vw_base_data_files exposes
-- it, vw_export_data_files ranks and filters by it. vw_user_data_files is
-- unchanged, only recreated (depends on vw_base_data_files).
-- ============================================================================

-- user_data_files.validated --------------------------------------------------
alter table user_data_files add column if not exists validated boolean not null default false;
comment on column user_data_files.validated is 'True when the validation process successfully finished (set by submit.py)';

-- backfill: the validator reported tests and submit did not fail
update user_data_files
   set validated = true
 where report_tests > 0
   and coalesce(error_code, 0) not between 260 and 270  -- submit failed (report missing, too small; 270 = move failed)
   and coalesce(error_code, 0) <> 11;                   -- submit.py:217, report not moved (raw task_code)

-- drop dependents first
drop view if exists vw_export_data_files;
drop view if exists vw_user_data_files;
drop view if exists vw_base_data_files;

-- vw_base_data_files ---------------------------------------------------------
create view vw_base_data_files
as select id,
    id_sep,
    id_users,
    concat(trim(both from ticket), '_', trim(both from file_name))::character varying(180) as stored_file_name,
        case
            when original_name is null or original_name::text = ''::text then file_name
            else original_name
        end as original_name,
    file_size,
    file_crc32,
    file_origin,
    user_receipt,
    report_errors,
    report_warns,
    validator_version,
    registered_at as uploaded_at,
    g_report_ready_at as validated_at,
    validated
   from user_data_files udf;

comment on view vw_base_data_files is 'Shared core columns/logic for vw_user_data_files and vw_export_data_files -- Refs #93. Neither specialized view depends on the other anymore, both depend on this instead.';
comment on column vw_base_data_files.validated is 'True when the validation process successfully finished (set by submit.py)';

alter table vw_base_data_files owner to canoa_power;
grant all on table vw_base_data_files to canoa_power;
grant select on table vw_base_data_files to canoa_connstr;

-- vw_user_data_files (unchanged) ---------------------------------------------
create view vw_user_data_files
as select b.id,
    b.id_sep,
    b.id_users,
    usr.username,
    usr.email,
    sep.sep_id,
    sep.sep_fullname,
    b.stored_file_name,
    b.original_name,
    b.file_size,
    b.file_crc32,
    b.file_origin,
    b.user_receipt,
    b.report_errors,
    b.report_warns,
    b.uploaded_at,
    b.validated_at
   from vw_base_data_files b
     join users usr on usr.id = b.id_users
     left join vw_scm_sep sep on b.id_sep = sep.sep_id
  order by b.id_users, b.uploaded_at desc;

comment on view vw_user_data_files is 'For received_files_mgmt.py';

alter table vw_user_data_files owner to canoa_power;
grant all on table vw_user_data_files to canoa_power;
grant select on table vw_user_data_files to canoa_connstr;

-- vw_export_data_files -------------------------------------------------------
create view vw_export_data_files
as select id,
    user_id,
    sep_id,
    scm_id,
    file_origin,
    file_name,
    sep_fullname,
    manager_name,
    uploaded_at,
    validated_at,
    report_errors,
    report_warns,
    validator_version,
    is_visible and file_name is not null and coalesce(validated, false) as is_exportable,
    validated
   from ( select b.id,
            b.id_users as user_id,
            sep.sep_id,
            sep.scm_id,
            sep.is_visible,
            sep.sep_fullname,
            usr.username as manager_name,
            b.file_origin,
            b.stored_file_name as file_name,
            b.uploaded_at,
            b.validated_at,
            b.report_errors,
            b.report_warns,
            b.validator_version,
            b.validated,
            row_number() over (partition by sep.sep_id order by b.validated desc nulls last, b.uploaded_at desc) as rn_recent,
            row_number() over (partition by sep.sep_id order by b.report_errors) as rn_lowest_errors
           from vw_scm_sep sep
             left join vw_base_data_files b on b.id_sep = sep.sep_id
             left join users usr on usr.id = sep.user_id
          where sep.is_visible or b.id is not null) udf_last_file
  where rn_recent = 1
  order by (not (is_visible and file_name is not null and coalesce(validated, false))) desc, (coalesce(report_errors, '-1'::integer)) desc;

comment on view vw_export_data_files is 'For scm_export_ui_display.py and scm_export_db.py. Shows a SEP if it is currently exportable (sep.is_visible) OR has real submission history, even if later marked non-exportable -- Refs #88.';

alter table vw_export_data_files owner to canoa_power;
grant all on table vw_export_data_files to canoa_power;
grant select on table vw_export_data_files to canoa_connstr;

-- ============================================================================
-- 2026-10-24 receiveFile message keys shared with revalidation -- Refs #61
-- rv_process.py returns the same keys as receive_file.py, but sep_validate
-- resolves them from the shared secError section. Copy, per locale.
-- ============================================================================

insert into ui_items (id_section, name, text, description)
select dst.id, itm.name, itm.text, 'copied from receiveFile -- Refs #61'
  from ui_items itm
  join ui_sections src on src.id = itm.id_section and src.name_lower = 'receivefile'
  join ui_sections dst on dst.id_locale = src.id_locale and dst.name_lower = 'secerror'
 where itm.name_lower = 'receivefilesubmit_error'
on conflict do nothing;

-- ============================================================================
-- 2026-11-05 file_origin 'S' (FILE_ORIGIN_STORAGE) -- Refs #61
-- a revalidation record's file is the stored one, kept in the uploaded folder
-- ============================================================================

comment on column user_data_files.file_origin is 'Indicates the source of the uploaded file, with ''L'' for local uploads, ''C'' for cloud downloads and ''S'' for a stored file, revalidated.';

-- ============================================================================
-- TODO 2026-11-05 (Miguel) revalidation report email -- Refs #61
-- create the texts section 'revalidatedFile_email' (as 'uploadedFile_email', but
-- "the validator was run again on the stored file"), then set it in rv_process.py
-- (cargo.email_texts).
-- ============================================================================

-- ============================================================================
-- db_version (production only, at commit time -- see the commit procedure)
-- insert into db_version (number, app_version, description) values ('?', 'β 6.03', '...');
-- ============================================================================

commit;

-- eof
