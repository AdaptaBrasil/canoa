-- update_canoa.sql
-- Pending DB changes, to apply first on canoa_dev, then on canoa (production).
--
-- Schema-independent: no `canoa.` prefixes. Set the target schema below, in the
-- `set search_path` line and in the guard's `expected`; a mismatch stops the script.
-- Unqualified names in the views are bound to it at creation time.
-- Run the whole script (DBeaver: Alt+X), not statement by statement.
-- Idempotent: it can run again on a DB that already has (part of) it.
--
-- Equipe da Canoa -- 2026
-- mgd 2026-10-24
-- cSpell:ignore secsuccess secerror receivefile receivefilesubmit_error uploadfilesuccess revalidatefilesuccess revalidatedfile
-- cSpell:ignore spdgrid sepvalidate formtitle grdbtnvalidateone estrat gicos uploadedfile revalidatefile uploadfileerror uploadfilezip uploadfileemail receivefileexception receivefileadmit

set search_path to canoa_dev;  -- ⚠️ canoa_dev for testing, canoa for production; same name in `expected` below

begin;

-- guard: stops (rollback) when the schema in effect is not the expected one
do $$
declare
  expected constant text := 'canoa_dev';  -- ⚠️ same name as the set search_path line
begin
  if current_schema() is distinct from expected then
    raise exception 'update_canoa.sql: wrong schema [%], expected [%]', current_schema(), expected;
  end if;
  raise notice 'START db [%] schema [%] version [%]', current_database(), current_schema(),
               (select number from db_version order by id desc limit 1);
end $$;

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
   and coalesce(error_code, 0) <> 11                    -- submit.py: report not found after the move (raw task_code)
   and not validated;                                   -- only the ones that are still false

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
-- 2026-11-06 UI texts: section revalidateFile (revalidate_file.py) and two
-- receiveFile keys that were missing (also for uploads) -- Refs #61
-- ============================================================================

insert into ui_sections (id_locale, name, title)
select loc.id, 'revalidateFile', 'Revalida&ccedil;&atilde;o de um arquivo armazenado'
  from ui_locales loc
on conflict do nothing;

insert into ui_items (id_section, name, text, description)
select sec.id, itm.name, itm.text, itm.description
  from ui_sections sec
  join (values
    ('revalidateFile', 'uploadFileSuccess',
     'A revalida&ccedil;&atilde;o (protocolo <code>{0}</code>) foi conclu&iacute;da. Um e-mail com os resultados foi enviado para <b>{1}</b>.',
     '{0} receipt, {1} report recipient'),
    ('revalidateFile', 'revalidateFileNotValidated',
     'Revalida&ccedil;&atilde;o {0} n&atilde;o conclu&iacute;da: a &uacute;ltima valida&ccedil;&atilde;o continuar&aacute; vigente.',
     '{0} receipt; processed, but the validation did not finish'),
    ('revalidateFile', 'revalidateFileNoRecord',
     'O registro [{1}] n&atilde;o foi encontrado [C&oacute;digo {0}].',
     '{0} error code, {1} record id'),
    ('revalidateFile', 'revalidateFileError',
     '<p>Ocorreu um erro [<code>C&oacute;digo {0}</code>] ao preparar a revalida&ccedil;&atilde;o.</p><p>Por favor, informe o texto abaixo.</p>',
     '{0} error code; lock folder or cleanup failed'),
    ('revalidateFile', 'revalidateFileAdmit_wait',
     'J&aacute; existe uma valida&ccedil;&atilde;o sua em andamento. Aguarde {1} minutos antes de enviar.',
     '{0} error code, {1} minutes left on the lock'),
    ('receiveFile', 'receiveFileAdmit_bad_lock',
     'N&atilde;o foi poss&iacute;vel iniciar a valida&ccedil;&atilde;o [<code>C&oacute;digo {0}</code>]. Por favor, tente novamente em alguns minutos.',
     '{0} error code; the processing lock could not be created'),
    ('receiveFile', 'spd_extract_error',
     'Erro [<code>C&oacute;digo {0}</code>] ao exportar os dados espaciais do setor para a valida&ccedil;&atilde;o.',
     '{0} error code; spdata.py')
  ) as itm (section, name, text, description) on sec.name_lower = lower(itm.section)
on conflict do nothing;

-- each module's section has its own copy of the keys it uses (secSuccess/secError: only common msgs)
-- receiveFile gets uploadFileSuccess from secSuccess (same text)
insert into ui_items (id_section, name, text, description)
select dst.id, itm.name, itm.text, 'copied from secSuccess'
  from ui_items itm
  join ui_sections src on src.id = itm.id_section and src.name_lower = 'secsuccess'
  join ui_sections dst on dst.id_locale = src.id_locale and dst.name_lower = 'receivefile'
 where itm.name_lower = 'uploadfilesuccess'
on conflict do nothing;

-- the revalidation success key was first named revalidateFileSuccess, now uploadFileSuccess
delete from ui_items where name_lower = 'revalidatefilesuccess';

-- revalidateFile gets the pipeline's keys (rv_process.py returns them, revalidate_file.py
-- resolves them in its own section), copied from receiveFile (same text)
insert into ui_items (id_section, name, text, description)
select dst.id, itm.name, itm.text, 'copied from receiveFile'
  from ui_items itm
  join ui_sections src on src.id = itm.id_section and src.name_lower = 'receivefile'
  join ui_sections dst on dst.id_locale = src.id_locale and dst.name_lower = 'revalidatefile'
 where itm.name_lower in ('uploadfileerror', 'uploadfilezip_unknown', 'uploadfilezip_corrupted', 'uploadfilezip_extraction_error',
                          'spd_extract_error', 'receivefilesubmit_error', 'uploadfileemail_failed',
                          'receivefileexception', 'receivefileadmit_bad_lock')
on conflict do nothing;

-- ============================================================================
-- 2026-11-06 revalidation report email: section revalidatedFile_email -- Refs #61
-- as uploadedFile_email (kind 4, email), but "validated again with the current
-- validator"; rv_process.py sets it in cargo.email_texts. Email texts: UTF-8.
-- placeholders (rv_email.py): {user} {receipt} {when} {version} {sep}
-- ============================================================================

insert into ui_sections (id_locale, id_kind, name, title)
select loc.id, 4, 'revalidatedFile_email', 'Informação da revalidação de um arquivo armazenado'
  from ui_locales loc
on conflict do nothing;

insert into ui_items (id_section, name, text, description)
select sec.id, itm.name, itm.text, itm.description
  from ui_sections sec
  join (values
    ('subject',
     'Canoa: Resultado da revalidação de protocolo [{receipt}] está anexado.',
     '{receipt}'),
    ('content',
     '<p>Olá, {user},</p>
<p>Esperamos que você esteja bem.</p>
<p>Os dados do setor {sep} foram validados novamente em {when}, com a versão atual do validador {version}.
O arquivo anexado a este e-mail contém os novos resultados (protocolo número {receipt}).</p>
<p>Se tiver alguma dúvida ou precisar de mais informações, estamos à disposição.</p>
<p>Atenciosamente,</p>
<p><b>Equipe Canoa</b></p>',
     '{user} {receipt} {when} {version} {sep}')
  ) as itm (name, text, description) on sec.name_lower = 'revalidatedfile_email'
on conflict do nothing;

-- the first version of the content had no {sep} (canoa_dev): add it
update ui_items itm
   set text = replace(itm.text, 'Os dados do seu setor foram', 'Os dados do setor {sep} foram'),
       description = '{user} {receipt} {when} {version} {sep}'
  from ui_sections sec
 where sec.id = itm.id_section and sec.name_lower = 'revalidatedfile_email'
   and itm.name_lower = 'content' and itm.text like '%Os dados do seu setor foram%';

-- ============================================================================
-- 2026-11-06 upload report email subject: "esta anexado" -> "está anexado" (email texts: UTF-8)
-- ============================================================================

update ui_items itm
   set text = replace(itm.text, 'esta anexado', 'está anexado')
  from ui_sections sec
 where sec.id = itm.id_section and sec.name_lower = 'uploadedfile_email'
   and itm.name_lower = 'subject' and itm.text like '%esta anexado%';

-- ============================================================================
-- 2026-11-10 sepValidate: current validator version after the title (own item formTitleValidator);
-- warning when it is not available. {{dv_version()}} is a Jinja function (see __init__.py),
-- sep_validate.py renders the item and appends it to formTitle.
-- ============================================================================

insert into ui_items (id_section, name, text, description)
select sec.id, 'validatorUnavailable',
       'N&atilde;o foi poss&iacute;vel obter a vers&atilde;o do validador. A revalida&ccedil;&atilde;o est&aacute; desativada.',
       'sep_validate.py: the current validator version is not available'
  from ui_sections sec
 where sec.name_lower = 'sepvalidate'
on conflict do nothing;

insert into ui_items (id_section, name, text, description)
select sec.id, 'formTitleValidator',
       'com o Validador <span class="code-text"><i>v</i> {{dv_version()}}</span>',
       'sep_validate.py: appended to formTitle'
  from ui_sections sec
 where sec.name_lower = 'sepvalidate'
on conflict do nothing;

-- the button revalidates the selected SEP's file (only if its validator version is not the current one)
update ui_items itm
   set text = 'Revalidar'
  from ui_sections sec
 where sec.id = itm.id_section and sec.name_lower = 'sepvalidate'
   and itm.name_lower = 'grdbtnvalidateone' and itm.text is distinct from 'Revalidar';

-- ============================================================================
-- 2026-11-11 spdGrid: key noRecord (spd_download.py [Baixar]; the key was missing in spdGrid and secError)
-- ============================================================================

insert into ui_items (id_section, name, text, description)
select sec.id, 'noRecord',
       'Registro n&atilde;o encontrado.',
       'spd_download.py: no record, or its file is missing'
  from ui_sections sec
 where sec.name_lower = 'spdgrid'
on conflict do nothing;

-- ============================================================================
-- 2026-11-11 passwordRecovery: "abra-o" must not wrap at the hyphen -> non-breaking hyphen (&#8209;), and the
-- space before it becomes &nbsp;, so the dash before it (" — abra-o") moves down with the word.
-- Handles both states (still "abra-o", or already "abra&#8209;o"), the dash itself is not touched.
-- ============================================================================

update ui_items itm
   set text = regexp_replace(itm.text, '(\s|&nbsp;)abra(-|&#8209;)o', '&nbsp;abra&#8209;o')
  from ui_sections sec
 where sec.id = itm.id_section and sec.name_lower = 'passwordrecovery'
   and itm.text ~ '(\s|&nbsp;)abra(-|&#8209;)o';

-- ============================================================================
-- db_version 5.14.0 for app 6.03 (idempotent: only once per DB)
-- ============================================================================

insert into db_version (number, app_version, description)
select '5.14.0', '6.03',
       'user_data_files.validated (set by submit.py), views rank/filter by it; file_origin S; '
       || 'ui sections revalidateFile & revalidatedFile_email, 2 missing receiveFile keys (Refs #61)'
 where not exists (select 1 from db_version where number = '5.14.0');

-- ============================================================================
-- db_updates: one row per run of this script (table created by hand, 2026-11-12).
-- Bump app_version and last_change (date of the newest section above) with each deploy.
-- ============================================================================

insert into db_updates (app_version, last_change, notes)
values ('6.10', '2026-11-11', 'spdGrid.noRecord, passwordRecovery abra-o; 5.14.0 row if missing');

do $$ begin raise notice 'END schema [%] version [%]', current_schema(), (select number from db_version order by id desc limit 1); end $$;

commit;

-- eof
