# Registration & Email Verification — Architecture & Reference

> Covers new-user registration and the separate, later-built email-verification flow —
> how they currently do (and don't) connect.
>
> Written after reading:
> `public/access_control/register.py`, `public/access_control/login.py`,
> `public/wtforms.py` (`RegisterForm`), `models/public/user.py`,
> `private/routes.py` (`email_addr_hub`), `private/access_control/email_addr_process.py`,
> `database/DDL/Canoa_DDL.sql` (the `users` BEFORE UPDATE trigger)
>
> mgd / Claude Sonnet 5 — 2026-07-24

---

## 1. Bird's-Eye View

Two flows exist, built about a year apart, and **today they don't talk to each other**:

```
REGISTER (public/access_control/register.py)
  RegisterForm → User(**request.form) → User.set_row()
    → shows "welcome" message on screen
    → NO email is sent (GitHub issue #1, still open)

LOGIN (public/access_control/login.py)
  login_user() succeeds regardless of email_verified
    → if verified:    redirect to /home
    → if NOT verified: show `msgVerifyEmail` warning page instead — login still
      succeeded, user is authenticated, just not sent home. NO email sent here either.

EMAIL VERIFICATION (private/routes.py: email_addr_hub, private/access_control/email_addr_process.py)
  Only reachable by clicking "Verificar endereço de e-mail" in the logged-in nav menu.
  This is the ONLY place that actually sends a verification email.
```

So a brand-new user today gets **zero emails** unless they log in, notice the warning
page, and manually find that nav menu item themselves.

---

## 2. Key Files

| File | Role |
|---|---|
| `public/access_control/register.py` | Registration route/handler — creates the `User` row |
| `public/wtforms.py` | `RegisterForm` (username, email, password, disabled) |
| `models/public/user.py` | `User` model — the token/verification columns live here |
| `public/access_control/login.py` | Login route — the only place that *checks* `email_verified` |
| `private/routes.py` (`email_addr_hub`) | Private route, the sole trigger for sending a verification email |
| `private/access_control/email_addr_process.py` | `send_and_wait_verify_token`, `explain_email_addr_proc`, `send_email_to_test_address` |
| `helpers/email_helper.py` | `send_email(recipients, ui_section, vars)` — generic, DB-text-driven email sender |
| `database/DDL/Canoa_DDL.sql` | `users` table's `BEFORE UPDATE` trigger — owns all the token/timestamp state transitions |
| `templates/includes/navigator.html.j2:244-246` | The only UI entry point into `email_addr_hub` |

---

## 3. Registration (`register.py`)

```python
def register():
    ...
    elif is_get: pass
    # post:
    elif User.get_where_name_is(user_name): ... # "userAlreadyRegistered"
    elif User.get_where_email_is(email): ...     # "emailAlreadyRegistered"
    elif not DB_len_val_for_pw.check(password): ...
    elif not DB_len_val_for_uname.check(user_name): ...
    else:
        new_user_rec = User(**request.form)
        User.set_row(new_user_rec)
        ui_db_texts.set_msg_success("welcome")
        # todo welcome e-mail with Token for email confirmation and login after confirmation
```

`RegisterForm` (`public/wtforms.py:46`) only collects `username`, `email`, `password`,
`disabled`. `User.__init__` (`models/public/user.py:73`) just `setattr`s whatever kwargs
it's given, hashing `password` along the way — no `id_role` is set here, and no
verification token is generated at this point either.

**The `# todo` comment is the ghost of a later feature.** It talks about "Token for
email confirmation" — but `verify_email_token`/`email_addr_hub` didn't exist yet when
this line was written (2024). It was never updated once that flow *was* built
(2026-04-02, commit `9497dd2`, "Hardened codebase..."), so it now reads like the
verification flow is planned here, when really it's a fully separate, already-working
subsystem that registration simply never calls into.

---

## 4. Login's role (`login.py:75-108`)

Login does **not** gate on `email_verified` — an unverified user still logs in
successfully (`login_user()` runs unconditionally once credentials check out). The only
difference is what they see afterward:

```python
if user_email_verified:
    return redirect_to(home_route())

ui_db_texts.set_msg_warn("msgVerifyEmail")
ui_db_texts.display_msg_only = True
```

No redirect to `email_addr_hub`, no email sent — just a warning page. The user has to
take the next step themselves.

---

## 5. The verification flow itself (`email_addr_hub`, `private/routes.py:452-497`)

Private route, requires login. A small state machine based on the user's current
token/verified state:

| Condition | Behavior |
|---|---|
| `user_rec.email_verified` | Sends a *test* email (`send_email_to_test_address`) — used to confirm mail delivery still works, not to (re)verify |
| No token yet, or token expired (`__does_user_need_token`), **and** no `uid` in URL | `explain_email_addr_proc` — shows an explanation/consent page first |
| Same, but `uid` present (user already clicked through the explanation) | `send_and_wait_verify_token` — **this is the one call that actually emails the token** |
| Active, non-expired token already pending | `verify_sent_token` — shows the "enter the code we sent you" form |

`has_token_expired()` (`email_addr_process.py:68`) checks `verify_email_sent_at` against
`sidekick.config.EMAIL_VERIFY_TOKEN_EXPIRES_HOURS` — relies entirely on the DB-set
timestamp, never a Python-side clock.

**The only UI entry point** is `navigator.html.j2:244-246`, a single dropdown item whose
label/tooltip flips between "Verificar endereço de e-mail" and "Confirmar envio de
e-mail" depending on `j_user.email_verified`.

---

## 6. The DB trigger (`Canoa_DDL.sql`, `users` `BEFORE UPDATE`)

All of the actual state transitions for `verify_email_token`/`email_verified_at` are
owned by the trigger, not Python:

```sql
new_token := trim(coalesce(new.verify_email_token, ''));
if (new_token ~ '^[0-9]{6}$') and new.verify_email_token is distinct from old.verify_email_token then
    -- a fresh 6-digit token was just set by the app -> stamp when it was sent
    new.verify_email_sent_at := now();
    new.email_verified_at    := null;
elsif old.verify_email_token is not null and (old.verify_email_token || '*' = new_token) then
    -- app appends '*' to the old token as its "user typed the right code" signal
    new.email_verified_at    := now();
    new.verify_email_sent_at := null;
    new.verify_email_token   := null;
elsif new_token != '' then
    -- anything else non-empty is junk -> discard
    new.verify_email_sent_at := null;
    new.verify_email_token   := null;
elsif new_token = '' and old.verify_email_token is not null then
    new.verify_email_sent_at := null;
end if;
```

The `'*'`-suffix is the "clearance sentinel": the app never sets `email_verified_at`
directly — it just writes `old_token + '*'` back to `verify_email_token`, and the
trigger recognizes that shape as "verification succeeded" and does the rest
(`email_verified` itself is a generated column: `email_verified_at IS NOT NULL`).

---

## 7. Known gap — GitHub issue #1

> "A mensagem `Bem-vindo` (_welcome_ no DB) que é mostrada ao terminar o processo de
> Registro, também deve ser enviada no e-mail confirmando o registro." — Miguel,
> 2024-04-16, still open as of 2026-07-24.

As written, the issue asks only for the existing on-screen "welcome" text to also go
out by email — it does **not** ask for the token/verification flow to be wired into
registration (that flow didn't exist yet in 2024). The `# todo` comment in
`register.py:60` conflates the two ideas, but they're separable:

- **Minimal fix**: after `User.set_row(new_user_rec)` succeeds, call the existing
  `send_email(recipients, ui_section, vars)` helper (same pattern as
  `email_addr_process.py`'s `_send_email`) reusing/adapting the "welcome" text.
- **Larger option**: also kick off `send_and_wait_verify_token`-equivalent logic right
  at registration, so a new user gets *both* a welcome email and an immediate
  verification token, instead of only discovering the verification flow the next time
  they log in and notice the warning page.

Not yet decided which scope Miguel wants — see `project_next_tasks.md` memory / chat
for the live discussion.

---

<small>_eof_</small>
