-- DROP VIEW canoa.vw_log_user_sep;

CREATE OR REPLACE VIEW canoa.vw_log_user_sep
AS SELECT id,
    id_sep,
    ( SELECT vw.sep_fullname
           FROM vw_scm_sep vw
          WHERE vw.sep_id = log.id_sep) AS sep_fullname,
    id_users,
    ( SELECT users.username
           FROM users
          WHERE users.id = log.id_users) AS user_name,
    id_users_prior,
    ( SELECT users.username
           FROM users
          WHERE users.id = log.id_users_prior) AS user_prior_name,
    done_at,
    done_by,
    ( SELECT users.username
           FROM users
          WHERE users.id = log.done_by) AS done_by_name,
    batch_code,
    operation,
    email_at,
    email_error
   FROM log_user_sep log
  ORDER BY done_at DESC;

COMMENT ON VIEW canoa.vw_log_user_sep IS 'Read-only audit-log grid for log_user_sep: resolves id_sep/id_users/id_users_prior/done_by to names for display. See carranca/models/private/log_user_sep_grid.py. `operation`s single-char code is decoded to a label in Python, not here.';

-- Permissions

ALTER TABLE canoa.vw_log_user_sep OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.vw_log_user_sep TO canoa_power;
GRANT SELECT ON TABLE canoa.vw_log_user_sep TO canoa_connstr;
