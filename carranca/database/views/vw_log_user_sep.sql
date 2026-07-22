-- DROP VIEW canoa.vw_log_user_sep;

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
