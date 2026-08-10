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
    , columnDefs: buildColumnDefs()
}; // gridOptions

// colMeta entries are keyed by field name, not position -- 'user_curr' (Gestor)
// is absent entirely for non-power users (see sep_grid.py), and 'spd_name' is a
// later addition, so don't assume a fixed column order/count.
function buildColumnDefs() {
    const colByName = Object.fromEntries(colMeta.map((c) => [c.n, c]));
    const col = (name, extra) => ({ field: name, headerName: colByName[name].h, flex: 3, ...extra });

    const defs = [
        { field: colCode, hide: true },
        { field: colIconUrl, hide: true },
        col('scm_name'),
        col('name'),
    ];

    if (userIsPower) {
        defs.push(col('user_curr'));
    }

    defs.push(col('spd_name'));
    defs.push(col('visible', {
        headerClass: 'text-center',
        cellStyle: { display: 'flex', justifyContent: 'center' },
        flex: 1,
    }));

    return defs;
}

const setActiveRow = (row, rowIx) => {
    if (!row) { return; }
    cargo[cargoKeys.row_index] = rowIx;
    cargo[cargoKeys.code] = row.data[colCode]
    if (icon.src != row.data[colIconUrl]) {
        icon.src = row.data[colIconUrl];
    }
    btnDownload.disabled = !row.data['spd_name'];
}

//-------------
//== Init
const gridContainer = document.getElementById(gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));
const btnDownload = /** @type {HTMLButtonElement} */(document.getElementById(btnDownloadId));
//== eof