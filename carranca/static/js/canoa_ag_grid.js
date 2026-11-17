/**
 * @preserve
 * canoa_ag_grid.js
 * version 0.3
 * 2026.11.10 -- 2026.11.16
 * Miguel Gastelumendi -- mgd + Anthropic Claude
 *
 * The common part of the ag-grid pages (sep_grid.js, scm_grid.js, spd_grid.js, sep_log_grid.js, sep_validate.js,
 * received_files_mgmt.js): the columns from colMeta, the formats by kind, the row selection and the active row
 * kept in `cargo`. What is specific of a grid is passed as options, see carranca/docs/grid-generalization.md.
 *
 * No globals: the data of the grid is the first argument, what the server sent
 *     { id, colMeta [{n, h}], rows, locale }; optional: cargo, cargoKeys, colCode (the active row is kept in `cargo`).
 *
 * Use:
 *     const { api } = CanoaAgGrid.create(Canoa.grid, {
 *         restoreRow: true,
 *         columns: { name: { flex: 3 }, qty: { kind: 'int' }, done_at: { kind: 'iso-datetime', width: '16rem' } },
 *     });
*/
// @ts-check
/* cSpell:locale en pt-br
 * cSpell:ignore numericColumn
 */
/// <reference path="./ts-check.js" />

const CanoaAgGrid = (() => {
    'use strict';

    //-------------
    // == Headers
    // ui_items.text is HTML-named-entity-encoded (see tools/encode-for-ui_items-table.py); ag-grid's headerName
    // renders as plain text, not innerHTML, so entities must be decoded (eg "Opera&ccedil;&atilde;o").
    // The DOM is used only if the text may have an entity (an `&` and a `;`).
    /**
     * @param {string} text
     * @param {any} [doc] the document; `null` where there is none (node tests)
     * @returns {string}
     */
    function decodeHtmlEntities(text, doc = typeof document === 'undefined' ? null : document) {
        if (!text || !doc) { return text; }
        if (!(text.includes('&') && text.includes(';'))) { return text; }
        const el = doc.createElement('textarea');
        el.innerHTML = text;
        return el.value;
    }

    //-------------
    // == Formats
    /** @param {number} n */
    function pad2(n) { return String(n).padStart(2, '0'); }

    /** @param {any} value a Date, or what `new Date()` accepts */
    function toDate(value) { return value instanceof Date ? value : new Date(value); }

    // ISO-style yyyy-mm-dd, not locale-dependent: local getters (not toISOString/getUTC*), so a date near
    // midnight doesn't shift to the adjacent day under a non-UTC timezone.
    /** @param {any} value */
    function isoDate(value) {
        if (!value) { return ''; }
        const d = toDate(value);
        return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
    }

    // same ISO style, plus hh:mm
    /** @param {any} value */
    function isoDateTime(value) {
        if (!value) { return ''; }
        const d = toDate(value);
        return `${isoDate(d)} ${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
    }

    // The formatter of each kind of column: the cell shows the formatted value, sorting uses the raw one
    /**
     * @param {string} locale
     * @returns {Record<string, (value: any) => string>}
     */
    function formatters(locale) {
        return {
            'int': value => (value == null ? '' : Number(value).toLocaleString(locale)),
            'percent': value => (value == null ? '' : `${Math.round(value)}%`),
            'date': value => (value ? toDate(value).toLocaleDateString(locale) : ''),
            'datetime': value => (value ? toDate(value).toLocaleString(locale) : ''),
            'iso-date': isoDate,
            'iso-datetime': isoDateTime,
        };
    }

    //-------------
    // == Columns
    // The ag-grid definition of a kind of column:
    //     text (default) | int | percent | date | datetime | iso-date | iso-datetime | right | center
    /**
     * @param {string} kind
     * @param {string} locale
     * @returns {Record<string, any>}
     */
    function kindDef(kind, locale) {
        const format = formatters(locale)[kind];
        switch (kind) {
            case 'text':
                return {};
            case 'int':
            case 'percent':
                // numericColumn right-aligns the header and the cells
                return { type: 'numericColumn', valueFormatter: params => format(params.value) };
            case 'date':
            case 'datetime':
            case 'iso-date':
            case 'iso-datetime':
                return { valueFormatter: params => format(params.value) };
            case 'right':
                return { type: 'rightAligned' };
            case 'center':
                // canoa.css: .grd-header-center .ag-header-cell-label { justify-content: center; }
                return { headerClass: 'grd-header-center', cellStyle: { display: 'flex', justifyContent: 'center' } };
            default:
                throw new Error(`CanoaAgGrid: unknown column kind [${kind}]`);
        }
    }

    // flex n (default 1), or a fixed width: px, '12rem' or 'header' (as wide as the header text, in rem).
    // `wrap` lets a header longer than its (narrow) column break into two lines.
    /**
     * @param {{flex?: number, width?: number | string, wrap?: boolean}} spec
     * @param {string} headerName
     * @param {number} remPx the root font size, in px
     * @returns {Record<string, any>}
     */
    function sizing(spec, headerName, remPx) {
        /** @type {Record<string, any>} */
        const def = {};
        if (spec.width === undefined) {
            def.flex = spec.flex ?? 1;
        } else {
            let px;
            if (spec.width === 'header') {
                px = Math.round(remPx * headerName.length);
            } else if (typeof spec.width === 'string' && spec.width.endsWith('rem')) {
                px = Math.round(remPx * parseFloat(spec.width));
            } else {
                px = Number(spec.width);
            }
            def.width = px;
            def.maxWidth = px;
        }
        if (spec.wrap) {
            def.wrapHeaderText = true;
            def.autoHeaderHeight = true;
        }
        return def;
    }

    // ag-grid's columnDefs from colMeta (the DB text colMetaInfo, in its order). A column with an empty header is hidden.
    // `columns`: the page's decisions, by field name: { kind, flex, width, wrap, hide, colDef };
    //     colDef is an ag-grid column definition merged last, it can override anything (the escape hatch).
    // `present`: the fields the rows have; a colMeta column the rows do not have is left out
    //     (eg `user_curr` of sep_grid, not sent to non-power users).
    /**
     * @param {{
     *   colMeta: {n: string, h: string}[], columns?: Record<string, any>, present?: Set<string> | null,
     *   userLocale: string, remPx: number, decode?: (text: string) => string, warn?: (msg: string) => void
     * }} p
     * @returns {Record<string, any>[]}
     */
    function buildColumnDefs(p) {
        const columns = p.columns ?? {};
        const decode = p.decode ?? decodeHtmlEntities;
        const warn = p.warn ?? console.warn;

        // a name in `columns` that is not in colMeta is a typo: say it
        const names = new Set(p.colMeta.map(c => c.n));
        for (const name of Object.keys(columns)) {
            if (!names.has(name)) { warn(`CanoaAgGrid: [${name}] is not in colMeta, ignored.`); }
        }

        const defs = [];
        for (const { n, h } of p.colMeta) {
            if (p.present && !p.present.has(n)) { continue; }
            const spec = columns[n] ?? {};
            const headerName = decode(h ?? '');
            if (!headerName || spec.hide) {
                defs.push({ field: n, headerName, hide: true, ...spec.colDef });
                continue;
            }
            defs.push({
                field: n,
                headerName,
                ...kindDef(spec.kind ?? 'text', p.userLocale),
                ...sizing(spec, headerName, p.remPx),
                ...spec.colDef,
            });
        }
        return defs;
    }

    //-------------
    // == Selection
    // The one place of the row selection syntax (issue #91: the string form is deprecated since ag-grid 32.2;
    // change it here, after checking the version that is loaded, and every grid follows).
    /** @param {boolean} keepSelected a row stays selected (no deselect by click) */
    function selectionOptions(keepSelected) {
        /** @type {Record<string, any>} */
        const def = { rowSelection: 'single' };
        if (keepSelected) { def.suppressRowDeselection = true; }
        return def;
    }

    //-------------
    // == Create
    /**
     * @param {{
     *   id: string, colMeta: {n: string, h: string}[], rows: any[], locale: string,
     *   cargo?: Record<string, any> | null, cargoKeys?: Record<string, string>, colCode?: string
     * }} data
     *   the data of the grid, what the server sent (the layout writes it as `Canoa.grid`):
     *   id: of the grid's element;  colMeta: the columns, name and header;  rows;  locale: of the user
     *   cargo, cargoKeys, colCode: only the grids that post the active row (eg to edit it)
     * @param {{
     *   columns?: Record<string, any>, keepSelected?: boolean, restoreRow?: boolean,
     *   onActiveRow?: (row: any, rowIndex: number) => void, onReady?: (params: any) => void,
     *   gridOptions?: Record<string, any>
     * }} [options]
     *   the page's decisions:
     *   columns: the page's column decisions, see buildColumnDefs
     *   keepSelected: a row stays selected (no deselect by click)
     *   restoreRow: on ready, select the row `cargo[cargoKeys.row_index]` (the active one before an edit), else the first
     *   onActiveRow: the page's own reaction to a new active row (an exception, eg icon, buttons)
     *   onReady: after the row was restored (eg set the focus on a cell)
     *   gridOptions: ag-grid options merged last (an exception, eg onSelectionChanged)
     */
    function create(data, options = {}) {
        if (!data) { throw new Error('CanoaAgGrid.create: the data of the grid is missing (`Canoa.grid`).'); }
        const cargo = data.cargo ?? null;
        const keys = data.cargoKeys ?? {};

        // the active row is kept in `cargo` (the page posts it), then the page's own reaction
        /**
         * @param {any} row
         * @param {number} rowIndex
         */
        function activate(row, rowIndex) {
            if (!row) { return; }
            if (cargo) {
                cargo[keys.row_index] = rowIndex;
                if (data.colCode !== undefined) { cargo[keys.code] = row.data[data.colCode]; }
            }
            if (options.onActiveRow) { options.onActiveRow(row, rowIndex); }
        }

        const remPx = parseFloat(getComputedStyle(document.documentElement).fontSize);
        /** @type {Record<string, any>} */
        const gridOptions = {
            ...selectionOptions(!!options.keepSelected),
            rowData: data.rows,
            columnDefs: buildColumnDefs({
                colMeta: data.colMeta,
                columns: options.columns,
                present: data.rows.length ? new Set(Object.keys(data.rows[0])) : null,
                userLocale: data.locale,
                remPx,
            }),
        };

        if (options.restoreRow || options.onReady) {
            gridOptions.onGridReady = (params) => {
                if (options.restoreRow) {
                    const rowIndex = cargo ? (cargo[keys.row_index] ?? 0) : 0;
                    const row = params.api.getDisplayedRowAtIndex(rowIndex);
                    if (row) {
                        setTimeout(() => { row.setSelected(true); activate(row, row.rowIndex); }, 20);
                    }
                }
                if (options.onReady) { options.onReady(params); }
            };
        }

        if (cargo || options.onActiveRow) {
            gridOptions.onCellFocused = (event) => {
                const hasRow = (event.rowIndex !== null) && !!event.api;
                const row = hasRow ? event.api.getDisplayedRowAtIndex(event.rowIndex) : null;
                activate(row, event.rowIndex);
            };
        }

        Object.assign(gridOptions, options.gridOptions);

        const api = agGrid.createGrid(document.getElementById(data.id), gridOptions);
        return { api, gridOptions, activate };
    }

    return { create, buildColumnDefs, decodeHtmlEntities, formatters, isoDate, isoDateTime, selectionOptions };
})();

// only in node: carranca/tools/canoa_ag_grid_test.js
if (typeof module !== 'undefined' && module.exports) { module.exports = CanoaAgGrid; }

//== eof
