/**
 * @preserve
 * sep_grid.js
 * version 0.4
 * 2026.05.21 --
 * Miguel Gastelumendi -- mgd
*/
// @ts-check
/* cSpell:locale en pt-br
 * cSpell:ignore mgmt
 */
/// <reference path="./ts-check.js" />

let removeCount = 0;
//-------------
// == Ag Grid
const gridOptions = {
    // rowSelection: { mode: 'singleRow', checkboxes: false },
    rowSelection: 'single',
    onGridReady: (params) => {
        const firstRow = params.api.getDisplayedRowAtIndex(cargo[cargoKeys.row_index]);
        if (firstRow) {
            setTimeout(() => { firstRow.setSelected(true); setActiveRow(firstRow, firstRow.rowIndex) }, 20);
        }
    },
    onCellFocused: (event) => {
        let row = (event.rowIndex === null) || !event.api ? null : event.api.getDisplayedRowAtIndex(event.rowIndex);
        setActiveRow(row, event.rowIndex)
    }
    , rowData: gridRows
    , columnDefs: [
        { field: colCode, hide: true },
        { field: colMeta[1].n, headerName: colMeta[1].h, flex: 3 },
        { field: colMeta[2].n, headerName: colMeta[2].h, flex: 3 },
    ]
}; // gridOptions

const setActiveRow = (row, rowIx) => {
    if (!row) { return; }
    cargo[cargoKeys.row_index] = rowIx;
    cargo[cargoKeys.code] = row.data[colCode]
}

//-------------
//== Init
const gridContainer = document.getElementById(gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));
//== eof