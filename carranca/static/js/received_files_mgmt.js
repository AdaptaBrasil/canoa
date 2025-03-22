/**
 * @preserve
 * sep_mgmt.js
 * version 0.4
 * 2024.10.18 -- 31
 * Miguel Gastelumendi -- mgd
*/
// @ts-check
/* cSpell:locale en pt-br
 * cSpell:ignore mgmt Rprt
 */

/// <reference path="./ts-check.js" />

let activeRow = null;
let btnFile = /** @type {HTMLButtonElement|null} */ (null);
let btnRprt = /** @type {HTMLButtonElement|null} */ (null);

window.addEventListener('beforeunload', (event) => {

});

//-------------
// == Basic Grid
const gridOptions = {
    onCellFocused: (event) => {
        activeRow = (event.rowIndex === null) ? null : api.getDisplayedRowAtIndex(event.rowIndex);
        if (activeRow) {
            if (!btnFile || !btnRprt) { ([btnFile, btnRprt] = defButtons()); }
            btnFile.disabled = !activeRow.data.data_f_found;
            btnRprt.disabled = !activeRow.data.report_found;
        }
    },
    rowData: rowData,
    columnDefs: [
        { field: colMeta[0].n, flex: 0, hide: true },
        { field: colMeta[1].n, flex: 0, hide: true },
        { field: colMeta[2].n, flex: 0, hide: true },

        //{ field: colMeta[3].n, headerName: colMeta[3].h, flex: 1, filter: isPower, hide: !isPower },
        { field: colMeta[3].n, headerName: colMeta[3].h, flex: 1, hide: true },
        {
            field: colMeta[4].n, headerName: colMeta[4].h, flex: 0,
            cellClassRules: {
                'grd-item-none': params => params.value == itemNone
            },
        },
        {
            field: colMeta[5].n, headerName: colMeta[5].h, flex: 1,
            cellClassRules: {
                'grd-item-none': params => {
                    const rowNode = params.api.getRowNode(params.rowIndex);
                    return rowNode ? !(rowNode.data.report_found && rowNode.data.data_f_found) : false;
                },
            },
        },
        { field: colMeta[6].n, headerName: colMeta[6].h, flex: 1 },
        {
            field: colMeta[7].n, headerName: colMeta[7].h, flex: 1,
            filter: true,
            valueFormatter: params => (params.value ? new Date(params.value).toLocaleString(dateFormat) : ''),
        },
        {
            field: colMeta[8].n, headerName: colMeta[8].h, flex: 1,
            type: 'rightAligned'
        },
        {
            field: colMeta[9].n, headerName: colMeta[9].h, flex: 1,
            type: 'rightAligned'
        }
    ]
};

//-------------
//== Init
const gridContainer = document.getElementById(gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));

/*
fetch('https://www.ag-grid.com/example-assets/space-mission-data.json')
    .then(response => response.json())
    .then((data: any) => gridApi.setGridOption('rowData', data))
*/
// eof