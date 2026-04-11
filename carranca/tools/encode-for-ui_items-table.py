"""
encode-for-ui_items-table.py
See table ui_items.text

This utility encodes UTF-8 text using named HTML entities for non-ASCII characters.
Specifically designed for UI items where legibility and HTML tag preservation are required.

Mapping logic:
  - ASCII (0-127): Maintained exactly as is (preserves <br>, <div>, etc.)
  - Non-ASCII (>127): Converted to Named Entities (e.g., &ccedil;, &atilde;)

Idea: mgd
Tandem work: Gemini & mgd
Date: 2026-04-10

Equipe Canoa
"""

# cSpell:words pyperclip


import html.entities
import sys

# Optional dependency for clipboard support
try:
    import pyperclip

    _CLIPBOARD_AVAILABLE = True
except ImportError:

    _CLIPBOARD_AVAILABLE = False

# AUTHORITATIVE BLUEPRINT: Pre-compute named entity mapping for codes > 127
_NAMED_ENTITY_MAP = {cp: f"&{name};" for cp, name in html.entities.codepoint2name.items() if cp > 127}


def encode_for_ui_items_table(text: str, copy_to_clipboard: bool = True) -> str:
    """
    Converts characters with diacritics into HTML named entities.
    ASCII characters (0-127) remain untouched.
    """
    # Default fallback for testing if no text is provided
    if not text:
        text = "O token de recuperação não<br> foi reconhecido."

    # Efficient translation using C-level mapping
    result = text.translate(_NAMED_ENTITY_MAP)

    if copy_to_clipboard:
        if _CLIPBOARD_AVAILABLE:
            try:
                pyperclip.copy(result)
            except Exception as e:
                print(f"Warning: Clipboard copy failed ({e})", file=sys.stderr)
        else:
            print("Warning: 'pyperclip' not installed. Result not copied.", file=sys.stderr)

    return result


def _encode(text: str, copy_to_clipboard: bool = True) -> str:
    """Helper wrapper for the encoding task."""
    return encode_for_ui_items_table(text, copy_to_clipboard)


if __name__ == "__main__":
    # Target text for conversion:
    input_text = "{nome}, confirma o encerramento da sessão?"  # Leave empty to use the default sample

    encoded_text = _encode(input_text)

    line_width = max(len(encoded_text), 40)
    print("-" * line_width)
    print(input_text)
    print(encoded_text)
    print("-" * line_width)

    if _CLIPBOARD_AVAILABLE and encoded_text:
        print("Result encoded and copied to clipboard.")

# eof

"""
sync-ui-entities.py
Database Synchronization Utility for Equipe Canoa

This script scans the 'ui_items' table and ensures all text follows
the named HTML entity standard for non-ASCII characters.

Logic:
1. Fetch current text from DB.
2. Run encode_for_ui_items_table.
3. If result != current, UPDATE the row.

Author: mgd (Equipe Canoa) & Gemini
Grant: CNPq
Date: 2026-04-10
"""
"""
import sys
# Import our co-authored utility
from encode_for_ui_items_table import encode_for_ui_items_table

# --- DATABASE CONFIGURATION ---
# Note: In production, these should come from your .env (CANOA_SQLALCHEMY_DATABASE_URI)
def get_db_connection():
    # Placeholder: Replace with your actual connection logic
    # import psycopg2 / pyodbc / sqlalchemy
    return None

def sync_table():
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection not configured.")
        return

    cursor = conn.cursor()

    # 1. Fetching only the necessary columns
    print("Fetching rows from ui_items...")
    cursor.execute("SELECT id, text FROM ui_items")
    rows = cursor.fetchall()

    updated_count = 0

    for row_id, db_text in rows:
        if not db_text:
            continue

        # 2. Run our idempotent conversion
        sanitized_text = encode_for_ui_items_table(db_text, copy_to_clipboard=False)

        # 3. Simple comparison: Only update if the text changed
        if sanitized_text != db_text:
            print(f"Update Required [ID {row_id}]: Found non-ASCII characters.")
            cursor.execute(
                "UPDATE ui_items SET text = %s WHERE id = %s",
                (sanitized_text, row_id)
            )
            updated_count += 1

    # Finalizing the transaction
    if updated_count > 0:
        conn.commit()
        print(f"Success: {updated_count} rows synchronized.")
    else:
        print("Verification Complete: All rows already compliant.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    sync_table()
"""
