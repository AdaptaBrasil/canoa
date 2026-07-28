-- DROP VIEW canoa.vw_user_data_files;

CREATE OR REPLACE VIEW canoa.vw_user_data_files
AS SELECT b.id,
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
   FROM vw_base_data_files b
     JOIN users usr ON usr.id = b.id_users
     LEFT JOIN vw_scm_sep sep ON b.id_sep = sep.sep_id
  ORDER BY b.id_users, b.uploaded_at DESC;

COMMENT ON VIEW canoa.vw_user_data_files IS 'For received_files_mgmt.py';

-- Permissions

ALTER TABLE canoa.vw_user_data_files OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_user_data_files TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_user_data_files TO canoa_connstr;
