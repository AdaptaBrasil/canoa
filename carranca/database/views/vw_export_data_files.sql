-- DROP VIEW canoa.vw_export_data_files;

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
   FROM ( SELECT b.id,
            b.id_users AS user_id,
            sep.sep_id,
            sep.scm_id,
            sep.is_visible,
            sep.sep_fullname,
            b.file_origin,
            b.stored_file_name AS file_name,
            b.registered_at AS uploaded,
            b.report_warns,
            b.report_errors,
            row_number() OVER (PARTITION BY b.id_sep ORDER BY b.registered_at DESC) AS rn_recent,
            row_number() OVER (PARTITION BY b.id_sep ORDER BY b.report_errors) AS rn_lowest_errors
           FROM vw_base_data_files b
             JOIN vw_scm_sep sep ON b.id_sep = sep.sep_id
          WHERE b.id_sep IS NOT NULL AND sep.is_visible) udf_last_file
  WHERE rn_recent = 1
  ORDER BY (COALESCE(report_errors, '-1'::integer)) DESC;

COMMENT ON VIEW canoa.vw_export_data_files IS 'For scm_export_ui_display.py and scm_export_db.py.';

-- Permissions

ALTER TABLE canoa.vw_export_data_files OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_export_data_files TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_export_data_files TO canoa_connstr;
