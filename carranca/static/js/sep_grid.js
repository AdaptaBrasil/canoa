/**
 * @preserve
 * sep_grid.js
 * version 0.4
 * 2025.05.23 --
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
        { field: colIconUrl, hide: true },
        { field: colMeta[2].n, headerName: colMeta[2].h, flex: 3 },
        { field: colMeta[3].n, headerName: colMeta[3].h, flex: 3 },
        { field: colMeta[4].n, headerName: colMeta[4].h, flex: 3 },
        {
            field: colMeta[5].n,
            headerName: colMeta[5].h,
            headerClass: 'text-center',
            cellStyle: { display: 'flex', justifyContent: 'center' },
            flex: 1
        },
    ]
}; // gridOptions

const setActiveRow = (row, rowIx) => {
    if (!row) { return; }
    cargo[cargoKeys.row_index] = rowIx;
    cargo[cargoKeys.code] = row.data[colCode]
    if (icon.src != row.data[colIconUrl]) {
        icon.src = row.data[colIconUrl];
    }
}

//-------------
//== Init
const gridContainer = document.getElementById(gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));
//== eof