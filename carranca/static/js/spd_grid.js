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
        { field: colCode, hide: true }, // id
        { field: colMeta[1].n, headerName: colMeta[1].h, flex: 4 }, // Nome
        { field: colMeta[2].n, headerName: colMeta[2].h, flex: 2 }, // Camada
        { field: colMeta[3].n, headerName: colMeta[3].h, flex: 2 }, // src
        { // qualidade
            field: colMeta[4].n,
            headerName: colMeta[4].h,
            valueFormatter: p => `${Math.round(p.value)}%`,
            cellStyle: { textAlign: 'right' },
            flex: 2
        },
        { // features
            field: colMeta[5].n,
            headerName: colMeta[5].h,
            valueFormatter: p => new Intl.NumberFormat(userLocale).format(p.value),
            cellStyle: { textAlign: 'right' },
            flex: 2
        },
        { field: colMeta[6].n, headerName: colMeta[6].h, flex: 3 }, // attributes
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