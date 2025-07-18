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
const icon = /** @type {HTMLImageElement} */(document.getElementById(iconID))


//-------------
// == Ag Grid
const gridOptions = {
    rowSelection: 'single',
    onGridReady: (params) => {
        const api = params.api
        const firstRow = api.getDisplayedRowAtIndex(cargo[cargoKeys.index]);
        if (firstRow) {
            setTimeout(() => { firstRow.setSelected(true); setActiveRow(firstRow, firstRow.rowIndex) }, 20);
        }
    },
    onCellFocused: (event) => {
        let row = (event.rowIndex === null) ? null : api.getDisplayedRowAtIndex(event.rowIndex);
        setActiveRow(row, event.rowIndex)
    }
    , rowData: gridRows
    , columnDefs: [
        { field: colCode, flex: 1, hide: true },
        { field: colIconUrl, flex: 1, hide: true },
        { field: colMeta[2].n, headerName: colMeta[2].h, hide: false, flex: 3 },
        { field: colMeta[3].n, headerName: colMeta[3].h, hide: false, flex: 4 },
        { field: colMeta[4].n, headerName: colMeta[4].h, hide: false, flex: 3 },
    ]
}; // gridOptions

const setActiveRow = (row, rowIx) => {
    if (!row) { return; }
    cargo[cargoKeys.index] = rowIx;
    cargo[cargoKeys.code] = row.data[colCode]
    if (icon.src != row.data[colIconUrl]) {
        icon.src = row.data[colIconUrl];
    }
}

//-------------
//== Init
const gridContainer = document.querySelector('#' + gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));
//== eof