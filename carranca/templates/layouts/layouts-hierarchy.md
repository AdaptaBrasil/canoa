# Canoa – Dialog Template Hierarchy

This document describes the **final HTML structure after inheritance**
from:

base → dialog
  → form → [login, ... ]
  - grid → [sep_grid, ...]

## 🧩 Template Chain Overview

| Template | Role | Defines |
|-----------|------|----------|
| `base.html.j2` | Application root | Global `<html>`, `<body>`, and blocks (`base_blc_main`, etc.) |
| `dialog.html.j2` | Core modal layout | Header, body, footer structure, and JavaScript hooks |
| `form.html.j2` | Handles `<form>` content | Input and submit logic, default footer button |
| `login.html.j2` | Specialized form | Login inputs and footer option links |

---
| Block                    | Source                          | Description                            |
| ------------------------ | ------------------------------- | -------------------------------------- |
| `dlg_blc_body`           | `form.html.j2` / `grid.html.j2` | Main dialog body (form inputs or grid) |
| `dlg_blc_footer_buttons` | `form.html.j2`                  | Buttons acting on form inputs          |
| `dlg_blc_footer_options` | `login.html.j2`                 | Informational links below buttons      |
| `dlg_blc_footer`         | `dialog.html.j2`                | Defines footer stacking and layout     |
| `grid_blc_footer`        | `grid.html.j2`                  | Custom grid footer controls            |
| `grid_blc_javascript`    | `grid.html.j2`                  | Grid setup and scripts                 |
| `grid_blc_forms`         | `grid.html.j2`                  | Optional supporting forms              |

🧠 Notes

- Buttons are action-oriented and belong directly under the form.
- Options (links) follow below, for secondary navigation or info.
- Inheritance is strictly one-directional; each layer adds content, not structure duplication.
- This layout keeps the dialog modular and predictable across all derived templates.


---

## 🧩 Final Rendered HTML Structure (Dialog Example)

```html
<div class="modal">
  <div class="modal-dialog">
    <div class="modal-content">

      <!-- HEADER -->
      <div class="modal-header">
        <h5 class="modal-title">
          [icon] Login
        </h5>
        <button class="btn-close"></button>
      </div>

      <!-- BODY -->
      <div class="modal-body">
        <form id="dlg-submit-form-id" method="post">
          <!-- Username -->
          <div class="form-group">
            <label>User Name</label>
            <input type="text" name="username">
          </div>

          <!-- Password -->
          <div class="form-group">
            <label>Password</label>
            <input type="password" name="password">
          </div>

          <!-- Remember me -->
          <div class="form-group">
            <input type="checkbox" name="remember_me"> Remember me
          </div>
        </form>
      </div>

      <!-- FOOTER -->
      <div class="modal-footer flex-column">

        <!-- Buttons (from form.html.j2) -->
        <div class="row justify-content-center" id="dlg_btns_container_id">
          <div class="col-auto">
            <button id="dlg_submit_ btn_id" type="submit" form="dlg-submit-form-id" class="btn btn-primary">
              Entrar
            </button>
          </div>
        </div>

        <!-- Options (from login.html.j2) -->
        <div class="row justify-content-center mt-2 w-100">
          <div class="col-6">
            <a href="/docs/privacyPolicy" class="form-link">Política de Privacidade</a>
          </div>
          <div class="col-6 text-end">
            <a href="/password_recovery" class="form-link">Esqueci minha senha</a>
          </div>
          <div class="col-6">
            <a href="/docs/termsOfUse" class="form-link">Termos de Uso</a>
          </div>
          <div class="col-6 text-end">
            <a href="/register" class="form-link">Fazer Cadastro</a>
          </div>
        </div>

      </div>
    </div>
  </div>
</div>

```code
base.html.j2
│
└── layouts/dialog.html.j2
│ • Defines dialog layout (header, body, footer)
│ • Declares blocks:
│ - Main .modal
│   - Dialog .modal-dialog
│       - base_blc_forms
│       - base_blc_forms
│ - dlg_blc_body
│ - dlg_blc_footer
│ - dlg_blc_footer_buttons
│ - dlg_blc_footer_options
│
├── layouts/form.html.j2
│ │ • Adds <form> and logic for backend / frontend modes
│ │ • Fills:
│ │ - dlg_blc_body (form and inputs)
│ │ - dlg_blc_footer_buttons (submit or close button)
│ │ • Declares:
│ │ - dlg_blc_footer_options (empty by default)
│ │
│ └── accounts/login.html.j2
│ • Specializes for login form
│ • Fills:
│ - frm_blc_inputs (username, password, remember me)
│ - dlg_blc_footer_options (links: privacy, forgot password, etc.)
│
└── layouts/grid.html.j2
│ • Specialized dialog to display ag-Grid tables
│ • Fills:
│ - dlg_blc_body (includes grid-body.html.j2)
│ • Declares:
│ - grid_blc_footer (custom footer controls)
│ - grid_blc_javascript (grid logic and setup)
│ - grid_blc_forms (auxiliary grid-related forms)
│ • Includes:
│ - includes/grid-header.html.j2 (JS/CSS imports)
│ - includes/grid-body.html.j2 (grid HTML container)