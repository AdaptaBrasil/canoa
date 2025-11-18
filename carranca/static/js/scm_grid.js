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

// let removeCount = 0;
//-------------

// https://www.ag-grid.com/javascript-data-grid/column-definitions/
// == Ag Grid
// rowSelection: { type: 'singleRow' }
const gridOptions = {
    rowSelection: 'single'
    , suppressRowDeselection: true
    , onGridReady: (params) => {
        const firstRow = params.api.getDisplayedRowAtIndex(cargo[cargoKeys.row_index]);
        if (firstRow) {
            setTimeout(() => {
                firstRow.setSelected(true);
                setActiveRow(firstRow, firstRow.rowIndex);
            }, 20);
        }
    }
    , onCellFocused: (event) => {
        let row = (event.rowIndex === null) || !event.api ? null : event.api.getDisplayedRowAtIndex(event.rowIndex);
        setActiveRow(row, event.rowIndex)
    }
    , rowData: gridRows
    , columnDefs: [
        { field: colCode, hide: true },
        { field: colMeta[1].n, headerName: colMeta[1].h, hide: false, flex: 2 },
        {
            field: colMeta[2].n,
            headerName: colMeta[2].h,
            hide: false,
            resizable: true,
            cellStyle: params => {
                return {
                    boxShadow: `inset 4em 0 0 ${params.value}`,
                    paddingLeft: '4.3em',
                }
            }
        },
        {
            field: colMeta[3].n,
            headerName: colMeta[3].h,
            flex: 1,
            cellStyle: { display: 'flex', justifyContent: 'center' },
            headerClass: 'ag-center-aligned-header',
        },
        { field: colMeta[4].n, headerName: colMeta[4].h, hide: false, flex: 2, type: 'numericColumn' }

    ]
}; // gridOptions

const setActiveRow = (row, row_index) => {
    if (!row) { return; }
    cargo[cargoKeys.row_index] = row_index;
    cargo[cargoKeys.code] = row.data[colCode]
}

//-------------
//== Init
const gridContainer = document.getElementById(gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));
//== eof