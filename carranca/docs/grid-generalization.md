# Grid generalization — one JS for all the ag-grid pages

**Status 2026-11-16: version 0.2, first page converted: `sep_validate`** (same grid in the browser; the other pages are unchanged).
Files: `static/js/canoa_ag_grid.js`, `tools/canoa_ag_grid_test.js` (14 tests, `node carranca/tools/canoa_ag_grid_test.js`), this doc.
Version 0.1 (2026-11-10) also carried a layout language inside `colMetaInfo`, `order`, `hiddenFields`, `align` and
`restoreCode`; dropped on 2026-11-12: no page needs them, and the code read "compiled". Add back one when a page asks for it.

## Why

Eight pages build the same ag-grid by hand. The same lines are copied in each `*_grid.js`:
`rowSelection`, `onGridReady` (select the row of `cargo`), `onCellFocused` → `setActiveRow`, `agGrid.createGrid(...)`.
The same decisions are made again per grid: date and number formats, column widths, header decoding, alignment.
Each fix (right-aligned numbers, `decodeHtmlEntities`, header centering) had to be done grid by grid.

## What is common and what is an exception

| Grid | Common part | Exception (stays in the page) |
|---|---|---|
| `sep_log_grid.js` | all | none (read only, no `cargo`) |
| `spd_grid.js` | all | none |
| `scm_grid.js` | all | `color` cell: a color chip (`boxShadow`) |
| `sep_grid.js` | all | `setActiveRow` also sets the icon and the [Baixar] button |
| `received_files_mgmt.js` | all | the `FileAvailableFilter`, cell class of a missing file |
| `sep_validate.js` | all | `onSelectionChanged` (the [Revalidar] rule), `grid-item-attention` cell class |
| `sep_mgmt.js` | selection, `cargo`, widths | editable select column, `valueSetter`, `doGridCargo` |
| `scm_export_ui_display.js` | grid options | the drag and drop of the reticule (unrelated to ag-grid) |

## The module: `CanoaAgGrid` (static/js/canoa_ag_grid.js)

A classic script (no `import`, like the other grid files). The page keeps its globals, as today:
`gridID`, `gridRows`, `colMeta` (`[{n, h}]`), `userLocale`; optional `cargo`, `cargoKeys`, `colCode`.

```js
const { api } = CanoaAgGrid.create({
    columns: { name: { flex: 3 }, qty: { kind: 'int' }, done_at: { kind: 'iso-datetime', width: '16rem' } },
    restoreRow: true,        // on ready, select the row cargo[cargoKeys.row_index] (the active one before an edit), else the first
    keepSelected: true,      // a row stays selected (no deselect by click)
    onActiveRow: (row, ix) => { ... },  // the page's own reaction to a new active row
    onReady: params => { ... },         // after the row was restored
    gridOptions: { onSelectionChanged }, // raw ag-grid options, merged last
});
```

**Columns** come from `colMeta` (the DB text `colMetaInfo`, in its order). Per column, in `columns`, by field name:

| Option | Effect |
|---|---|
| `kind` | `text` (default), `int`, `percent`, `date`, `datetime`, `iso-date`, `iso-datetime`, `right`, `center` |
| `flex: n` | flex size (default 1) |
| `width` | px, `'12rem'` or `'header'` (as wide as the header text); `wrap: true` also wraps the header |
| `hide: true` | hidden column (a column with an empty header in `colMetaInfo` is hidden anyway) |
| `colDef` | ag-grid column definition merged **last**: it can override anything (the escape hatch) |

Rules built in:
- Headers go through `decodeHtmlEntities` (the DOM is used only if the text has an `&` and a `;`).
- A `colMeta` column that the rows do not have is left out (eg `user_curr` of `sep_grid`, not sent to non-power users).
- A name in `columns` that is not in `colMeta` is reported in the console (a typo is noticed).
- Never calls `sizeColumnsToFit()`: only `flex` or `width`, never both mixed (ag-grid docs say they fight).
- The row selection syntax lives in one function, `selectionOptions()`: issue #91 becomes a one-place change.

## Each grid, with the module

`sep_log_grid.js` (about 45 lines → 5):
```js
CanoaAgGrid.create({ keepSelected: true, columns: { done_at: { kind: 'datetime', flex: 2 } } });
```

`spd_grid.js`:
```js
CanoaAgGrid.create({
    restoreRow: true,
    columns: {
        id: { hide: true }, spd_name: { flex: 4 }, layer_name: { flex: 2 }, layer_crs: { flex: 2 },
        layer_health: { kind: 'percent', flex: 2 }, features_count: { kind: 'int', flex: 2 }, attributes: { flex: 3 },
    },
});
```

`sep_validate.js` (the common part; `onSelectionChanged` and the cell classes stay):
```js
CanoaAgGrid.create({
    columns: {
        sep_fullname: { flex: 2 }, manager_name: { flex: 1 },
        uploaded_at: { kind: 'iso-date', width: '10rem', wrap: true },
        validated_at: { kind: 'iso-datetime', width: '16rem', wrap: true, colDef: { cellClassRules: { 'grid-item-changed': isChangedToday } } },
        validator_version: { width: '10rem', wrap: true, colDef: { cellClassRules: { 'grid-item-attention': isOtherValidatorVersion } } },
        report_errors: { kind: 'int', width: 'header' }, report_warns: { kind: 'int', width: 'header' },
    },
    gridOptions: { onSelectionChanged },
});
```

`sep_grid.js` (the icon and the button are the exception, in `onActiveRow`):
```js
CanoaAgGrid.create({
    restoreRow: true,
    columns: { id: { hide: true }, icon_file_name: { hide: true }, scm_name: { flex: 3 }, name: { flex: 3 },
               user_curr: { flex: 3 }, spd_name: { flex: 3 }, visible: { kind: 'center', flex: 1 } },
    onActiveRow: row => { icon.src = row.data[colIconUrl]; btnDownload.disabled = !row.data.spd_name; },
});
```

`scm_grid.js`: same, plus `color: { colDef: { cellStyle: p => ({ boxShadow: `inset 4em 0 0 ${p.value}`, paddingLeft: '4.3em' }) } }`.

`received_files_mgmt.js`, `scm_export_ui_display.js` and `sep_mgmt.js` follow the same pattern; their exceptions are the ones in the table above.

## What it takes to adopt it (not done)

1. `canoa.css`: add the header centering class (the Bootstrap `text-center` and ag-grid's `ag-center-aligned-header` never worked):
   ```css
   .grd-header-center .ag-header-cell-label { justify-content: center; }
   ```
2. In each page template, `<script src="...canoa_ag_grid.js">` before the page script. The page script shrinks to the `create({...})` call.
3. Adopt one grid at a time, simplest first: `sep_log_grid`, `spd_grid`, `scm_grid`, `sep_grid`, `received_files_mgmt`, `sep_validate`; `sep_mgmt` last.
   Each one is tested in the browser against the old behavior (widths, alignment, row restored after returning from an edit).
4. When a page is converted, delete its old copy of the common code; `ag-grid-helper.js` (an unused ES module with the old `columnApi`) can go.

## Things this settles from the "ag-grid revision" list

Header centering (class above), `flex` vs `sizeColumnsToFit` (never mixed), right-aligned numbers (`kind: 'int'`),
`decodeHtmlEntities` shared (with Miguel's `&` and `;` shortcut), the selection syntax in one place (#91).

## Decided 2026-11-16: the page data goes in `Canoa.grid`

Loose globals today: each grid template writes `colMeta`, `gridRows`, `gridID` and `userLocale` in an inline `<script>`
(the edit grids also `cargo`, `cargoKeys`, `colCode`); the same lines are in eight templates. The values come from Jinja,
so the inline script stays, but as one object on the namespace that already exists, `window.Canoa` (`canoa.js`):

```js
Canoa.grid = {
    id: '{{ grid_id | default("ag-grid-id") }}',
    colMeta: {{ grid_col_meta | default([]) | tojson | safe }},
    rows: {{ grid_data | default([]) | tojson | safe }},
    locale: '{{ userLocale }}',
};
```

- **One reader.** Only `CanoaAgGrid.create()` reads them: the `typeof cargo !== 'undefined'` checks and the matching
  `var` lines of `ts-check.js` go away.
- **Order.** First on `sep_validate` (converted, still with the globals), before a second grid adopts the module:
  the other pages are then converted once, straight to the final shape.
- **Layout.** `grid.html.j2` can write the common four only after the last page is converted (a page not converted
  still reads the globals); until then each converted page writes its own `Canoa.grid`.
  Page-only values (eg `validatorReady`) stay in the page.

## Open questions

- **`colMeta` order.** The columns follow the order of the DB text `colMetaInfo`. Today each grid fixes its own order in code.
  If the DB order is not the one wanted, fix the DB text (an `order` option existed in 0.1; add it back if a text can't change).
- **Hidden columns.** A column hides when its header is empty or with `hide: true`. Check each `colMetaInfo` for the id/icon columns:
  a non-empty header there needs `hide: true`.
- **ag-grid version.** It is loaded unpinned from the CDN (`grid-header.html.j2:14`). `selectionOptions()` still uses the string syntax;
  the new object syntax must be checked against the version that is loaded before changing it (#91).
- **Row restored by id, not by index.** After an edit the grid selects `cargo[row_index]`; no Python route sends the edited
  row's code yet (`grid_init_row` is never passed). When one does, add a `restoreCode` option (0.1 had one) and
  look the row up by its code.
- **Column widths.** Set in the page's `columns` option; nothing is measured, nothing comes from the DB. Decision 2026-11-10:
  leave it as is, see it in real use. Ideas for later: a default width per `kind`, ag-grid's `autoSizeStrategy`
  (check it against the version that is loaded).
- **Python side.** Not touched: `js_ui_dictionary` already gives every grid its `colMeta`. A shared Python helper for the
  row preparation (`to_code`, ISO dates) is a possible next step, after the JS.
