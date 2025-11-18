
/**
 * @preserve
 * received_files_mgmt.js
 * version 0.4
 * 2024.10.18 -- 31, 2025.03
 * Miguel Gastelumendi -- mgd
*/
// @ts-check
/* cSpell:locale en pt-br
 * cSpell:ignore Rprt gridOptions
 */

/// <reference path="./ts-check.js" />

class FileAvailableFilter {
    /* this code was provided by Gemini */
    init = (params) => {
        this.params = params;
        this.setupGui();
    }

    setupGui = () => {
        this.gui = document.createElement('div');
        this.gui.innerHTML = `
            <div style="padding: 4px;">
                <div class="ag-filter-body-wrapper">
                    <label style="display: block; margin-bottom: 5px;">
                        <input type="radio" name="foundFilter" value="all" checked> Todos
                    </label>
                    <label>
                        <input type="radio" name="foundFilter" value="found"> Disponíveis
                    </label>
                </div>
            </div>
        `;

        this.rbAll = this.gui.querySelector('input[value="all"]');
        this.rbFound = this.gui.querySelector('input[value="found"]');
        this.rbAll.addEventListener('change', this.onRbChanged);
        this.rbFound.addEventListener('change', this.onRbChanged);
    }
    onRbChanged = () => this.params.filterChangedCallback();
    getGui = () => this.gui;
    doesFilterPass = (params) => this.rbFound.checked ? params.data.report_found || params.data.data_f_found : true
    isFilterActive = () => this.rbFound.checked;
    getModel = () => this.isFilterActive() ? { state: 'found' } : null;
    setModel = (model) => {
        if (model?.state === 'found') {
            this.rbFound.checked = true;
        } else {
            this.rbAll.checked = true;
        }
        this.onRbChanged();
    }
}

//-------------
// == Basic Grid
const stats_width = Math.round(parseFloat(getComputedStyle(document.documentElement).fontSize) * (colMeta[8].h).length);
const gridOptions = {
    rowSelection: 'single',
    onGridReady: (params) => {
        const firstRow = params.api.getDisplayedRowAtIndex(0);
        if (firstRow) { setTimeout(() => { setActiveRow(firstRow); firstRow.setSelected(true); }, 20); }
    },
    onCellFocused: (event) => {
        let row = (event.rowIndex === null) || !event.api ? null : event.api.getDisplayedRowAtIndex(event.rowIndex);
        setActiveRow(row)
    },
    rowData: gridRows,
    columnDefs: [
        { field: colMeta[0].n, hide: true },
        { field: colMeta[1].n, hide: true },
        { field: colMeta[2].n, hide: true },
        { field: colMeta[3].n, hide: true },
        { // scm/sep
            field: colMeta[4].n,
            headerName: colMeta[4].h,
            flex: 2,
            cellClassRules: { 'grid-item-none': params => params.value == itemNone },
        },
        { // file name
            field: colMeta[5].n,
            headerName: colMeta[5].h,
            flex: 3,
            cellClassRules: {
                'grid-item-none': params => {
                    const rowNode = params.api.getRowNode(params.rowIndex);
                    return rowNode ? !(rowNode.data.report_found || rowNode.data.data_f_found) : false;
                },
            },
            filter: FileAvailableFilter,
        },
        { field: colMeta[6].n, headerName: colMeta[6].h, flex: 0 },
        {
            field: colMeta[7].n, headerName: colMeta[7].h, flex: 0,
            valueFormatter: params => (params.value ? new Date(params.value).toLocaleString(dateFormat) : ''),
            filter: true,
        },
        {
            field: colMeta[8].n, headerName: colMeta[8].h,
            // Use 3rem for width: compute at runtime based on root font-size
            width: stats_width,
            maxWidth: stats_width,
            type: 'rightAligned',
        },
        {
            field: colMeta[9].n, headerName: colMeta[9].h,
            width: stats_width,
            maxWidth: stats_width,
            type: 'rightAligned',
        }
    ]
};

//-------------
//== Init
const gridContainer = document.getElementById(gridID);
agGrid.createGrid(gridContainer, gridOptions);


// eof