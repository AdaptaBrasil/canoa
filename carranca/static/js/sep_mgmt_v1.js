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
let selectList = [...initialList];
let removeCount = 0
const ignoreList = [itemRemove, itemNone];
const icon = /** @type {HTMLImageElement} */(document.getElementById("dlg-var-icon-id"))

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
        if (activeRow) {
            icon.src = activeRow.data[colIconSrc]
        }
    }
    , rowData: rowData
    , columnDefs: [
        { field: colMeta[0].n, flex: 0, hide: true },
        { field: colIconSrc, flex: 0, hide: true },
        { field: colMeta[2].n, headerName: colMeta[2].h, flex: 1 },
        {
            field: colMeta[3].n,
            headerName: colMeta[3].h,
            flex: 2,
            cellClassRules: {
                'grd-item-none': params => params.value === itemNone,
                'grd-item-exist': params => assignedList.includes(params.value) && (params.data[colUserNew] == itemNone),
            },
        },
        {
            field: colMeta[4].n,
            headerName: colMeta[4].h,
            flex: 2,
            editable: true,
            cellClass: 'grd-col-sep_new',
            cellClassRules: {
                'grd-item-none': params => params.value === itemNone,
                'grd-item-remove': params => params.value === itemRemove,
                'grd-item-added': params => addedList.includes(params.value),
            },
            cellEditor: 'agSelectCellEditor',
            cellEditorParams: params => {
                const sepOld = params.data[colUserCurr]
                let lst = [...selectList].filter(a => a != sepOld);
                if (!lst.includes(params.value) && !ignoreList.includes(params.value)) { lst.push(params.value) }
                lst = sortList(lst).concat((sepOld == itemNone) ? [itemNone] : ignoreList)
                return { values: lst };
            },
            valueSetter: (params) => {
                const oldValue = params.oldValue;
                const newValue = params.newValue;
                if (newValue === oldValue) return false;

                if (!ignoreList.includes(oldValue)) {
                    selectList.push(oldValue)
                    need_refresh(params.api, oldValue) // remove back-color
                    assignedList = assignedList.filter(item => item !== oldValue);

                }
                if (!ignoreList.includes(newValue)) {
                    selectList = selectList.filter(item => item !== newValue);
                    assignedList.push(newValue)
                    need_refresh(params.api, newValue) // set back-color
                }
                if (oldValue === itemRemove) { removeCount--; }
                if (newValue === itemRemove) { removeCount++; }
                params.data[colUser] = newValue;
                btnGridSubmit.disabled = (assignedList.length == 0) && (removeCount == 0)
                return true;
            }
        },
        {
            field: colMeta[5].n
            , headerName: colMeta[5].h
            , valueFormatter: params => (params.data[colMeta[5].n] ? params.data[colMeta[5].n].toLocaleDateString(dateFormat) : '')
            , flex: 1
        }
    ]
}; // gridOptions


//-------------
//== Init
const gridContainer = document.querySelector('#' + gridID);
const api = /** type {Object} */(agGrid.createGrid(gridContainer, gridOptions));


//-------------
// == Actions
const _itemAdd = (sepNew) => {
    let result = false;
    if (sepNew == '') {
        // ignore
    } else if (exists_sep(sepNew)) {
        alert(`O nome '${sepNew}' já está na lista.`);
    } else {
        sortList(addedList, sepNew);
        sortList(selectList, sepNew);
        activeRow.setDataValue(colUserNew, sepNew);
        result = true;
    }
    return result;
}

const gridAdd = () => {
    if (getActiveCellValue() == '') { return }
    let sep_new = getPrompt(formAdd);
    _itemAdd(sep_new);
}

const gridEdit = () => {
    const cellValue = getActiveCellValue()
    if (cellValue == '') {
        // ignore
    } else if (initialList.includes(cellValue) || ignoreList.includes(cellValue)) {
        alert(formCantEdit)
    } else {
        let sep_new = getPrompt(formEdit, cellValue);
        if (sep_new !== cellValue) {
            selectList = selectList.filter(item => item !== cellValue);
            addedList = addedList.filter(item => item !== cellValue);
            _itemAdd(sep_new);
        }
    }
}

const gridCargo = ( /** @type {string} */ id) => {
    api.stopEditing();
    const elResponse = /** @type {HTMLInputElement} */(document.getElementById(id));
    if (!elResponse) { return false; }
    // TODO Error msg
    const gridCargo = [];
    api.forEachNode(node => gridCargo.push(node.data));
    const cargo = JSON.stringify(
        {
            actions: { none: itemNone, remove: itemRemove },
            grid: gridCargo,
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
const getPrompt = (msg, _default) => {
    api.stopEditing();
    const text = trim_it(prompt(msg, _default))
    return text
}
const toLowerPlus = (/** @type {string} */ str) => str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
const exists_sep = (/** @type {string} */ item) => {
    const _item = toLowerPlus(item).trim();
    const lst = initialList.concat(ignoreList).concat(addedList);
    const exits = lst.filter(a => toLowerPlus(a) === _item);
    return exits.length > 0;
}
const trim_it = (/** @type {string|null} */ item) => ((item == null) || (item.trim() === '')) ? '' : item.trim();
const getActiveCellValue = () => {
    const cellValue = trim_it(activeRow == null ? null : activeRow.data[colSepNew]);
    if (cellValue == '') {
        alert('Clique na coluna [SE Novo] na linha onde deseja adicionar ou editar.');
    }
    return cellValue;
}

// eof