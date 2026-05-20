# Reference Model: Project Canoa Architecture


`carranca\private\email_token_process.py » verify_sent_token`

This is the module that serves as the authoritative blueprint for refactoring and new feature
development within the Canoa environment (fev/2006)
---

## Key Implementation Standards

### 1. Text Management

- Uses `ui_db_texts_manager.py` and the `UIDBTexts` class.
- Avoid hardcoded strings; always fetch from the database using section IDs (e.g., section 32).

### 2. Message Handling

Implements the `Msg` introspection class for standardized UI messaging:

- `add_msg_error()`
- `add_msg_success()`
- *(etc.)*
- Automatic clearing of existing message states using `msg.all_keys()`.

### 3. Error Encapsulation

Follows the **Fatal Exception** pattern:

- In case of failure, generates a unique log ID.
- Displays a structured *"Situação Inesperada"* UI block to the user.
- Does **not** expose sensitive code details.

### 4. Template Rendering

Demonstrates the **manual override** for template filenames:

- Decouples database section names from physical `.html.j2` files.

### 5. Coding Style

| Convention | Example |
|---|---|
| `Pascal_Snake` for type aliases | `DB_Texts` |
| Proper case for UI strings via HTML entities | `&aacute;` ? á |
| Defensive dictionary handling | `.pop(key, None)` |


---
<small>_eof_</small>



