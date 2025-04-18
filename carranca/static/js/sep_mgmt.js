/**
 * @preserve
 * sep_mgmt.js
 * version 0.4
 * 2024.10.18 -- 31
 * Miguel Gastelumendi -- mgd
*/
// @ts-check
/* cSpell:locale en pt-br
 * cSpell:ignore mgmt
 */

/// <reference path="./ts-check.js" />

let activeRow = null;
let addedList = [];
let assignedList = [];
let removeCount = 0
const ignoreList = [itemRemove, itemNone];
const icon = /** @type {HTMLImageElement} */(document.getElementById(iconID))
const col_data = 5

window.addEventListener('beforeunload', (event) => {
    if (assignedList.length > 0) {
        event.preventDefault();
    }
});

//-------------
// == Basic Grid
const gridOptions = {
    onCellFocused: (event) => {
        activeRow = (event.rowIndex === null) ? null : api.getDisplayedRowAtIndex(event.rowIndex);
        if (activeRow && (icon.src != activeRow.data[colIconSrc]))
            icon.src = activeRow.data[colIconSrc];
    },
    onGridReady: (params) => {
        const col_0 = params.api.getAllDisplayedColumns()[0];
        params.api.setFocusedCell(0, col_0.getColId());
    }
    , rowData: gridRows
    , columnDefs: [
        { field: colMeta[0].n, flex: 0, hide: true },
        { field: colIconSrc, flex: 0, hide: true },
        { field: colMeta[2].n, headerName: colMeta[2].h, flex: 2 },
        { field: colMeta[3].n, headerName: colMeta[3].h, flex: 1 },
        {
            field: colMeta[4].n
            , headerName: colMeta[4].h
            , valueFormatter: params => (params.data[colMeta[4].n] ? params.data[colMeta[4].n].toLocaleDateString(dateFormat) : '')
            , flex: 1
        },
        {
            field: colMeta[col_data].n,
            headerName: colMeta[col_data].h,
            flex: 1,
            editable: true,
            cellClass: 'grd-col-sep_new',
            cellClassRules: {
                'grd-item-none': params => params.value === itemNone,
                'grd-item-remove': params => params.value === itemRemove,
                'grd-item-added': params => addedList.includes(params.value),
            },
            cellEditor: 'agSelectCellEditor',
            cellEditorParams: params => {
                const userCurr = params.data[colUserCurr]
                let lst = [...userList].filter(a => a != userCurr);
                //if (!lst.includes(params.value) && !ignoreList.includes(params.value)) { lst.push(params.value) }
                //lst = sortList(lst).concat((userCurr == itemNone) ? [itemNone] : ignoreList)
                return { values: lst };
            },
            valueSetter: (params) => {
                const oldValue = params.oldValue;
                const newValue = params.newValue;
                if (newValue === oldValue) return false;

                if (!ignoreList.includes(oldValue)) {
                    need_refresh(params.api, oldValue) // remove back-color
                    assignedList = assignedList.filter(item => item !== oldValue);

                }
                if (!ignoreList.includes(newValue)) {
                    assignedList.push(newValue)
                    need_refresh(params.api, newValue) // set back-color
                }
                if (oldValue === itemRemove) { removeCount--; }
                if (newValue === itemRemove) { removeCount++; }
                params.data[colUserNew] = newValue;
                btnGridSubmit.disabled = (assignedList.length == 0) && (removeCount == 0)
                return true;
            }
        },
    ]
}; // gridOptions


//-------------
//== Init
const gridContainer = document.querySelector('#' + gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));


//-------------
// == Actions
const gridCargo = ( /** @type {string} */ id) => {
    api.stopEditing();
    const elResponse = /** @type {HTMLInputElement} */(document.getElementById(id));
    if (!elResponse) { return false; }
    // TODO Error msg
    const gridCargo = [];
    api.forEachNode(node => {
        if (node.data && node.data[colMeta[col_data].n] !== itemNone) {
            gridCargo.push(node.data);
        }
    });
    const cargo = JSON.stringify(
        { // se carranca\private\sep_mgmt_save.py that parses the cargo
            [cargoKeys.actions]: { [cargoKeys.none]: itemNone, [cargoKeys.remove]: itemRemove },
            [cargoKeys.grid]: gridCargo,
        }
    );
    elResponse.value = cargo
    assignedList = [] // don't ask on leave
    return true
}
//-------------
// == Helpers
const sortList = (lst, newItem) => {
    if (newItem != null) { lst.push(newItem) }
    lst.sort((a, b) => a.localeCompare(b));
    return lst;
};
const need_refresh = (api, value) => {
    if (assignedList.includes(value)) {
        setTimeout(() => { api.refreshCells({ columns: [colUserCurr], force: true }) }, 0)
    }
};
const toLowerPlus = (/** @type {string} */ str) => str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
const trim_it = (/** @type {string|null} */ item) => ((item == null) || (item.trim() === '')) ? '' : item.trim();
const getActiveCellValue = () => {
    const cellValue = trim_it(activeRow == null ? null : activeRow.data[colUserNew]);
    if (cellValue == '') {
        alert('Clique na coluna [SE Novo] na linha onde deseja adicionar ou editar.');
    }
    return cellValue;
}

// eof