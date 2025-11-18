# Canoa/Carranca Project File Index
# Canoa/Carranca Module Index

This document provides an index and a brief description of the key files within the `carranca` application, focusing on the private modules responsible for handling core business logic.
This document provides an index of the application's core features, grouping together the back-end (`.py`), front-end (`.js`), and template (`.j2`) files that constitute each module.

---

## 📁 `carranca/private/`

This directory contains the core back-end logic for authenticated users.
### Schema (Esquema) Modules

### Schemas (Esquemas) Management
Modules related to the management and display of Schemas.

Handles the creation, display, and organization of Schemas and their relationship with SEPs.
-   **`scm_grid`**: A grid to display all available Schemas.
    -   `carranca/private/scm_grid.py`: Back-end logic to fetch and prepare schema data for the grid.
    -   `carranca/static/js/scm_grid.js`: Front-end JavaScript for AG-Grid configuration and user interactions.
    -   `carranca/templates/private/scm_grid.j2`: Jinja2 template that defines the HTML structure for the schema grid page.

-   **Schema Grid & Edit**
    -   `carranca/private/scm_grid.py`: Back-end logic to fetch and display a grid of all available Schemas.
    -   `carranca/private/scm_new_edit.py`: Manages the form for creating a new Schema or editing an existing one. Handles data validation and persistence.
-   **`scm_new_edit`**: A form for creating a new Schema or editing an existing one.
    -   `carranca/private/scm_new_edit.py`: Back-end logic to handle form submission, data validation, and saving schema information.
    -   `carranca/static/js/scm_new_edit.js`: Front-end JavaScript for form enhancements, particularly for the color input.
    -   `carranca/templates/private/scm_new_edit.j2`: Jinja2 template that renders the schema creation/edition form.

-   **Schema Export UI**
    -   `carranca/private/scm_export_ui_show.py`: Renders the user interface that allows admins to visually arrange SEPs within Schemas for database export.
    -   `carranca/private/scm_export_ui_save.py`: Saves the new visual order of SEPs within a Schema as defined by the user in the export UI.
    -   `carranca/private/scm_export_db.py`: Handles the final step of exporting the structured Schema and SEP data to the database.
    -   `carranca/private/scm_data.py`: A helper module to collect and structure all data related to Schemas and their associated SEPs.
    -   `carranca/private/scm_import.py`: The counterpart to export; defines logic to import schema data from a JSON structure.
-   **`scm_export`**: A user interface for admins to visually arrange SEPs within Schemas and export the final structure.
    -   `carranca/private/scm_export_ui_show.py`: Renders the initial UI with all schemas and their associated SEPs.
    -   `carranca/private/scm_export_ui_save.py`: Saves the new visual order of SEPs within a schema.
    -   `carranca/private/scm_export_db.py`: Handles the final database export of the schema structure.
    -   `carranca/templates/private/scm_export.j2`: Jinja2 template for the visual arrangement page.
    -   `carranca/static/js/scm_export.js`: Front-end JavaScript for drag-and-drop functionality and handling save/export actions.

### SEPs (Setores Estratégicos) Management
### SEP (Setor Estratégico) Modules

Handles the logic for Strategic Sectors (SEPs), including their display, editing, and icon management.
Modules related to the management and display of Strategic Sectors (SEPs).

-   **SEP Grid & Edit**
    -   `carranca/private/sep_grid.py`: Back-end logic to fetch and display a grid of SEPs, including user assignments.
    -   `carranca/private/sep_new_edit.py`: Manages the form for creating a new SEP or editing an existing one. Handles complex logic for different user roles (power vs. normal user).
-   **`sep_grid`**: A grid to display all available SEPs and their assigned managers.
    -   `carranca/private/sep_grid.py`: Back-end logic to fetch and prepare SEP data for the grid.
    -   `carranca/static/js/sep_grid.js`: Front-end JavaScript for AG-Grid configuration and handling user interactions.
    -   `carranca/templates/private/sep_grid.j2`: Jinja2 template that defines the HTML structure for the SEP grid page.

-   **SEP Icons**
    -   `carranca/private/sep_icon.py`: Manages the lifecycle of SEP icon files. Creates, deletes, and provides URLs for SVG icons, including default/fallback icons.
    -   `carranca/private/SepIconMaker.py`: A helper class that defines the properties (e.g., folder, file names) and generates the SVG content for system icons (empty, error, none).
    -   `carranca/private/SepIcon.py`: A data class holding basic information about a SEP's icon.
-   **`sep_new_edit`**: A form for creating a new SEP or editing an existing one.
    -   `carranca/private/sep_new_edit.py`: Back-end logic to handle form submission, data validation, and icon uploads.
    -   `carranca/templates/private/sep_new_edit.j2`: Jinja2 template that renders the SEP creation/edition form.
    -   `carranca/static/js/sep_new_edit.js`: Front-end JavaScript for handling icon uploads and other dynamic form behaviors.

### Core Application Logic
### Other Core Modules

Core modules for routing, user session management, and data validation processes.

-   `carranca/private/routes.py`: The central router for all private endpoints. Defines all URLs accessible after a user has logged in (e.g., `/home`, `/sep_grid`, `/scm_grid`).
-   `carranca/private/receive_file.py`: Handles the initial file upload process for data validation. It performs preliminary checks on uploaded files or Google Drive links before passing them to the validation pipeline.
-   `carranca/private/AppUser.py`: A wrapper class around Flask-Login's `current_user` to provide application-specific properties and methods for the logged-in user (e.g., `is_power`, `seps`).
-   `carranca/private/JinjaUser.py`: A "slimmer" version of `AppUser` designed to be safely passed to Jinja2 templates, exposing only necessary and non-sensitive user information.
-   `carranca/private/wtforms.py`: Defines all WTForms classes used in the private section for forms like file receiving, password changes, and SEP/Schema editing.

### Utility & Helper Classes

-   `carranca/private/UserSep.py`: A data class representing a SEP from a user's perspective, including UI-related properties.
-   `carranca/private/IdToCode.py`: A simple utility class for obfuscating integer IDs into base-N strings for use in public-facing URLs.
-   `carranca/private/RolesAbbr.py`: An `Enum` that defines abbreviations for user roles (Admin, Support, etc.), making role-based logic clearer.

---
### Logbook & Staging Info

-   `mgd-logbook.txt`: A detailed developer logbook tracking changes, to-dos, and version history since the project's inception.
-   `SAtelier-info/satelier-infra-resume.md`: A comprehensive summary of the project's staging infrastructure, server setup, port forwarding rules, and deployment history.

-   **`receive_file`**: The user-facing form for uploading a file or providing a Google Drive link for data validation.
    -   `carranca/private/receive_file.py`: Back-end logic that performs initial checks and passes the file to the validation pipeline.
    -   `carranca/templates/private/receive_file.j2`: Jinja2 template that renders the file upload form.
    -   `carranca/static/js/receive_file.js`: Front-end JavaScript to manage the state of the form (e.g., toggling between file upload and URL input).
