-- DROP VIEW canoa.vw_export_data_files;

CREATE OR REPLACE VIEW canoa.vw_export_data_files
AS SELECT id,
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
    is_visible AND file_name IS NOT NULL AS is_exportable
   FROM ( SELECT b.id,
            b.id_users AS user_id,
            sep.sep_id,
            sep.scm_id,
            sep.is_visible,
            sep.sep_fullname,
            usr.username AS manager_name,
            b.file_origin,
            b.stored_file_name AS file_name,
            b.uploaded_at,
            b.validated_at,
            b.report_errors,
            b.report_warns,
            b.validator_version,
            row_number() OVER (PARTITION BY sep.sep_id ORDER BY b.uploaded_at DESC) AS rn_recent,
            row_number() OVER (PARTITION BY sep.sep_id ORDER BY b.report_errors) AS rn_lowest_errors
           FROM vw_scm_sep sep
             LEFT JOIN vw_base_data_files b ON b.id_sep = sep.sep_id
             LEFT JOIN users usr ON usr.id = sep.user_id
          WHERE sep.is_visible OR b.id IS NOT NULL) udf_last_file
  WHERE rn_recent = 1
  ORDER BY (NOT (is_visible AND file_name IS NOT NULL)) DESC, (COALESCE(report_errors, '-1'::integer)) DESC;

COMMENT ON VIEW canoa.vw_export_data_files IS 'For scm_export_ui_display.py and scm_export_db.py. Shows a SEP if it is currently exportable (sep.is_visible) OR has real submission history, even if later marked non-exportable -- Refs #88.';

-- Permissions

ALTER TABLE canoa.vw_export_data_files OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_export_data_files TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_export_data_files TO canoa_connstr;
