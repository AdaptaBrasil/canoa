/**
 * @preserve
 * sep_validate.js
 * version 0.1
 * 2026.07.28
 * Miguel Gastelumendi -- mgd
*/
// @ts-check
/* cSpell:locale en pt-br
 */
/// <reference path="./ts-check.js" />

// ui_items.text is HTML-named-entity-encoded (see tools/encode-for-ui_items-table.py);
// ag-grid's headerName renders as plain text, not innerHTML, so entities must be
// decoded here or they'd show literally (eg "Vers&atilde;o").
/** @param {string} text */
const decodeHtmlEntities = (text) => {
    const el = document.createElement('textarea');
    el.innerHTML = text;
    return el.value;
};

// https://www.ag-grid.com/javascript-data-grid/column-definitions/
// == Ag Grid (single-row selection feeds [Validar Um]; [Validar Todos] needs no selection --
// both still just POST to the same under-development stub in sep_validate.py, see #61)

const selectedSepIdInput = /** @type {HTMLInputElement} */ (document.getElementById('selected-sep-id'));
const btnValidateOne = /** @type {HTMLButtonElement} */ (document.getElementById('btn-validate-one-id'));

/** @param {any} event */
const onSelectionChanged = event => {
    const row = event.api.getSelectedRows()[0];
    selectedSepIdInput.value = row ? row.sep_id : '';
    btnValidateOne.disabled = !row;
};

// Only genuinely variable-length text columns flex; short/fixed-shape columns get a computed
// width instead -- same balance already used in received_files_mgmt.js for its stat columns.
/** @type {Record<string, number>} */
const flexByField = { sep_fullname: 2, manager_name: 1 };

// received_files_mgmt.js's trick: size a narrow column from its own header length (rem-based,
// so it scales with root font-size), since the header is the widest thing that column shows.
const remPx = parseFloat(getComputedStyle(document.documentElement).fontSize);
/** @param {string} headerText */
const widthFromHeader = headerText => Math.round(remPx * headerText.length);

/** @type {Set<string>} */
const headerSizedFields = new Set(['report_errors', 'report_warns']);

// validator_version/uploaded_at: content (eg "2026-07-28") is much shorter than their headers --
// size these columns to the content instead, and let the (now too-long-for-the-column) header
// wrap onto two lines rather than force the column wide.
/** @type {Set<string>} */
const thinContentFields = new Set(['validator_version', 'uploaded_at']);
const thinContentWidth = Math.round(remPx * 10);

// validated_at shows date+time (eg "2026-07-28 14:32"), wider than the date-only columns above.
const validatedAtWidth = Math.round(remPx * 16);

// "just processed today" signal: same limegreen text canoa.css's .grid-item-changed already
// uses elsewhere in the app, reused here rather than inventing a new highlight class.
/** @param {Date} value */
const isToday = value => {
    const today = new Date();
    return value.getFullYear() === today.getFullYear()
        && value.getMonth() === today.getMonth()
        && value.getDate() === today.getDate();
};

/** @param {any} params */
const isChangedToday = params => params.value && isToday(new Date(params.value));

// ag-grid's built-in 'numericColumn' type right-aligns both the header and the cells
/** @type {Record<string, string>} */
const typeByField = { report_errors: 'numericColumn', report_warns: 'numericColumn' };

/** @param {any} params */
const formatInt = params => params.value != null ? params.value.toLocaleString(userLocale) : '';

// ISO-style yyyy-mm-dd, not locale-dependent -- uses local getters (not toISOString/getUTC*)
// so a date near midnight doesn't shift to the adjacent day under a non-UTC timezone.
/** @param {any} params */
const formatIsoDate = params => {
    if (!params.value) return '';
    const d = new Date(params.value);
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${mm}-${dd}`;
};

// same ISO style, plus hh:mm -- validated_at needs the time too, not just the date.
/** @param {any} params */
const formatIsoDateTime = params => {
    if (!params.value) return '';
    const d = new Date(params.value);
    const hh = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${formatIsoDate(params)} ${hh}:${min}`;
};

/** @type {Record<string, (params: any) => string>} */
const formatterByField = {
    uploaded_at: formatIsoDate,
    validated_at: formatIsoDateTime,
    report_errors: formatInt,
    report_warns: formatInt,
};

const gridOptions = {
    rowSelection: 'single'
    , onSelectionChanged: onSelectionChanged
    , rowData: gridRows
    , columnDefs: colMeta.map(({ n, h }) => {
        const headerName = decodeHtmlEntities(h);
        const sizing = n === 'validated_at'
            ? { width: validatedAtWidth, maxWidth: validatedAtWidth, wrapHeaderText: true, autoHeaderHeight: true }
            : thinContentFields.has(n)
                ? { width: thinContentWidth, maxWidth: thinContentWidth, wrapHeaderText: true, autoHeaderHeight: true }
                : headerSizedFields.has(n)
                    ? { width: widthFromHeader(headerName), maxWidth: widthFromHeader(headerName) }
                    : { flex: flexByField[n] ?? 1 };
        return {
            field: n,
            headerName,
            ...sizing,
            ...(typeByField[n] ? { type: typeByField[n] } : {}),
            ...(formatterByField[n] ? { valueFormatter: formatterByField[n] } : {}),
            ...(n === 'validated_at' ? { cellClassRules: { 'grid-item-changed': isChangedToday } } : {}),
        };
    })
}; // gridOptions

//-------------
//== Init
const gridContainer = document.getElementById(gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));
//== eof
