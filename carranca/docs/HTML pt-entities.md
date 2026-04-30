# Canoa UI Text Storage and Encoding Reference


The **Canoa project** is designed from the ground up to be **easily translatable and language‑agnostic**.

All user‑facing text — including HTML pages, forms, labels, messages, and help content — is **stored in the database**, rather than embedded directly in HTML templates.

Each HTML page or logical UI scope is represented by an entry in table `ui_section`.
All textual elements belonging to that section are stored in table `ui_items` and rendered dynamically by the UI layer (see ``carranca\common\UIDBTexts.py``).

To ensure consistency, portability, and tooling simplicity, all text stored in `ui_items` and `ui_section` **must use ASCII characters only** (`0–9`, `a–z`, `A–Z`).
Any character outside this range — such as Portuguese vowels with diacritics — must be encoded using **HTML named entities**.

This approach:
- avoids character‑encoding ambiguity,
- simplifies diffs and reviews,
- enables safe reuse of content across languages and renderers,
- and supports automated translation workflows.

For automated or bulk conversion of UTF‑8 text into ASCII‑only form, use the helper script:

``\carranca\tools\encode-for-ui_items-table.py``


### Common Portuguese text fragments (encoding patterns)

| Common fragment | Encoded form |
|-----------------|--------------|
| ção | &ccedil;&atilde;o |
| ções | &ccedil;&atilde;es |
| são | s&atilde;o |
| ação | a&ccedil;&atilde;o |
| edição | edi&ccedil;&atilde;o |
| inserção | inser&ccedil;&atilde;o
| extensão | extens&atilde;o |
| descrição | descri&ccedil;&atilde;o |
| atualização | atualiza&ccedil;&atilde;o |
| configuração | configura&ccedil;&atilde;o |


### Portuguese vowels with diacritics & cedilla

The table below serves as a **reference for Portuguese vowels with diacritics** and their corresponding **HTML named entities**, to assist when authoring, reviewing, or validating text stored in the DB.


| Letter| Diacritic        | HTML entity |
|------:|------------------|-------------|
| c     | cedilla          | &ccedil;    |


| Vowel | Diacritic        | HTML entity |
|------:|------------------|-------------|
| **a** | acute            | &aacute;    |
| a     | grave            | &agrave;    |
| a     | circumflex       | &acirc;     |
| a     | tilde            | &atilde;    |
| a     | diaeresis&dagger;| &auml;      |
| a     | diaeresis&dagger;| &auml;      |
| **e** | acute            | &eacute;    |
| e     | circumflex       | &ecirc;     |
| e     | diaeresis&dagger;| &euml;      |
| **i** | acute            | &iacute;    |
| i     | circumflex       | &icirc;     |
| i     | diaeresis&dagger;| &iuml;      |
| **o** | acute            | &oacute;    |
| o     | circumflex       | &ocirc;     |
| o     | tilde            | &otilde;    |
| o     | diaeresis&dagger;| &ouml;      |
| **u** | acute            | &uacute;    |
| u     | circumflex       | &ucirc;     |
| u     | diaeresis&dagger;| &uuml;      |


---
&dagger; *diaeresis*
<small>entries are non-native to PT but commonly appear in names,
loanwords, and technical text.</small>

---
<small>_eof_</small>
