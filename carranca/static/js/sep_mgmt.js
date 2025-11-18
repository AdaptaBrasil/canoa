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
// ! export { }; // Tells the checker this is a module, so `gridContainer` can be is other js files ;--)

let activeRow = null;
let removeCount = 0
let assignedList = /** @type {string[]} */([]);
const ignoreList = [itemNone];
const icon = /** @type {HTMLImageElement} */(document.getElementById(iconID))

// window.addEventListener('beforeunload', (event) => {
//     if (assignedList.length > 0) {
//         event.preventDefault();
//     }
// });

//-------------
// == Basic Grid
const gridOptions = {
    rowSelection: 'single',
    onGridReady: (params) => {
        const api = params.api
        const firstRowNode = api.getDisplayedRowAtIndex(0);
        if (firstRowNode) { setTimeout(() => { firstRowNode.setSelected(true); }, 20); }
        setTimeout(() => { api.setFocusedCell(0, colUserNew); }, 40);
    },
    onCellFocused: (event) => {
        activeRow = (event.rowIndex === null) ? null : api.getDisplayedRowAtIndex(event.rowIndex);
        if (activeRow && (icon.src != activeRow.data[colIconUrl]))
            icon.src = activeRow.data[colIconUrl];
    }
    , rowData: gridRows
    , columnDefs: [
        { field: colMeta[0].n, hide: true },
        { field: colIconUrl, hide: true },
        { field: colUserCurr, hide: true },
        { field: colMeta[3].n, headerName: colMeta[3].h, hide: false, flex: 3 },
        {
            field: colUserNew,
            headerName: colMeta[4].h,
            flex: 2,
            editable: true,
            cellClass: 'grd-col-sep_new',
            cellClassRules: {
                'grid-item-remove': params => ((params.value === itemNone) && (params.value !== params.data[colUserCurr])),
                'grid-item-none': params => ((params.value === itemNone) && (params.value === params.data[colUserCurr])),
                'grid-item-changed': params => ((params.value !== itemNone) && (params.value !== params.data[colUserCurr])),
            },
            cellEditor: 'agSelectCellEditor',
            cellEditorParams: params => {
                const user = params.data[colUserNew]
                let lst = [...userList].filter(a => a !== user || a === itemNone);
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
                if (oldValue === itemNone) { removeCount--; }
                if (newValue === itemNone) { removeCount++; }
                params.data[colUserNew] = newValue;
                btnGridSubmit.disabled = (assignedList.length == 0) && (removeCount == 0);
                Canoa.dataModified = !btnGridSubmit.disabled;

                return true;
            }
        },
        {
            field: colMeta[5].n
            , headerName: colMeta[5].h
            , valueFormatter: params => (params.data[colMeta[5].n] ? params.data[colMeta[5].n].toLocaleDateString(dateFormat) : '')
            , flex: 2
        },
        {
            field: colMeta[6].n
            , headerName: colMeta[6].h
            , headerClass: 'text-center'
            , flex: 1
            , cellStyle: { display: 'flex', justifyContent: 'center' }
        },

    ]
}; // gridOptions


//-------------
//== Init
const gridContainer = document.getElementById(gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));


//-------------
// == Actions
const doGridCargo = () => {
    api.stopEditing();
    const elResponse = /** @type {HTMLInputElement} */(document.getElementById(respID));
    if (!elResponse) { return false; }
    // TODO Error msg
    /** @type {Array<Object>} */
    const payLoad = [];
    api.forEachNode(node => {
        if (node.data && (node.data[colUserNew] !== node.data[colUserCurr])) {
            payLoad.push(node.data);
        }
    });
    const cargo = JSON.stringify(
        { // se carranca/private/sep_mgmt_save.py that parses the cargo
            [cargoKeys.actions]: { [cargoKeys.none]: itemNone },
            [cargoKeys.cargo]: payLoad,
        }
    );
    elResponse.value = cargo
    Canoa.dataModified = false;
    // assignedList = [] // don't ask on leave
    return true
}
//-------------
const need_refresh = (api, value) => {
    if (assignedList.includes(value)) {
        setTimeout(() => { api.refreshCells({ columns: [colUserNew], force: true }) }, 0)
    }
};

// eof