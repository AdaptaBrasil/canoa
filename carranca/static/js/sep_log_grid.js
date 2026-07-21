/**
 * @preserve
 * sep_log_grid.js
 * version 0.1
 * 2026.07.18
 * Miguel Gastelumendi -- mgd
*/
// @ts-check
/* cSpell:locale en pt-br
 */
/// <reference path="./ts-check.js" />

// ui_items.text is HTML-named-entity-encoded (see tools/encode-for-ui_items-table.py);
// ag-grid's headerName renders as plain text, not innerHTML, so entities must be
// decoded here or they'd show literally (eg "Opera&ccedil;&atilde;o").
/** @param {string} text */
const decodeHtmlEntities = (text) => {
    const el = document.createElement('textarea');
    el.innerHTML = text;
    return el.value;
};

// https://www.ag-grid.com/javascript-data-grid/column-definitions/
// == Ag Grid (read-only log: no cargo, no row actions)
/** @type {Record<string, number>} */
const flexByField = { done_at: 1, operation: 1, curr_user_name: 2, prior_user_name: 2, done_by_name: 2 };

/** @type {Record<string, (params: any) => string>} */
const formatterByField = {
    done_at: params => params.value ? new Date(params.value).toLocaleString(userLocale) : ''
};

const gridOptions = {
    rowSelection: 'single'
    , suppressRowDeselection: true
    , rowData: gridRows
    , columnDefs: colMeta.map(({ n, h }) => ({
        field: n,
        headerName: decodeHtmlEntities(h),
        flex: flexByField[n] ?? 1,
        ...(formatterByField[n] ? { valueFormatter: formatterByField[n] } : {}),
    }))
}; // gridOptions

//-------------
//== Init
const gridContainer = document.getElementById(gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));
//== eof
