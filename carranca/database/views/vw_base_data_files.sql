-- DROP VIEW canoa.vw_base_data_files;

CREATE OR REPLACE VIEW canoa.vw_base_data_files
AS SELECT id,
    id_sep,
    id_users,
    concat(TRIM(BOTH FROM ticket), '_', TRIM(BOTH FROM file_name))::character varying(180) AS stored_file_name,
        CASE
            WHEN original_name IS NULL OR original_name::text = ''::text THEN file_name
            ELSE original_name
        END AS original_name,
    file_size,
    file_crc32,
    file_origin,
    user_receipt,
    report_errors,
    report_warns,
    validator_version,
    registered_at AS uploaded_at,
    g_report_ready_at AS validated_at
   FROM user_data_files udf;

COMMENT ON VIEW canoa.vw_base_data_files IS 'Shared core columns/logic for vw_user_data_files and vw_export_data_files -- Refs #93. Neither specialized view depends on the other anymore, both depend on this instead.';

-- Permissions

ALTER TABLE canoa.vw_base_data_files OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_base_data_files TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_base_data_files TO canoa_connstr;
