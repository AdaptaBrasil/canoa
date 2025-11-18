/**
 * @preserve
 * scm_export.js
 * version 0.1
 * 2025.09.01 --
 * Miguel Gastelumendi -- mgd
*/
// @ts-check
/* cSpell:locale en pt-br
 * cSpell:ignore
 */
/// <reference path="./ts-check.js" />


// SEP grid arrangement
document.addEventListener('DOMContentLoaded', () => {
   let draggedItem = /** @type {HTMLSpanElement | null} */(null);
   function initializeDragAndDrop() {
      const SCHEMA = 0
      const SEP = 1
      const gridImages = /** @type {HTMLSpanElement[]} */ (Array.from(document.querySelectorAll('.reticule-item-hot')));

      /** Retrieve the Schema o Sep of and Id ('scm:sep')
       *  @type {(part: number, s: HTMLSpanElement) => string|undefined} */
      const _get = (part, s) => s.firstElementChild?.id.split(':')[part];

      /** Compare the Schema or Sep of two items.
       *  @type {(part: number, a: HTMLSpanElement, b: HTMLSpanElement) => boolean} */
      const same = (part, a, b) => _get(part, a) === _get(part, b);

      /** Determines if a item can be dropped: both belong to the same schema
       *  @type {(item: HTMLSpanElement) => boolean} */
      const canDrop = (item) => (draggedItem != null) && (draggedItem !== item) && same(SCHEMA, draggedItem, item);

      gridImages.forEach(item => {
         item.addEventListener('dragstart', () => {
            draggedItem = item;
            setTimeout(() => { (item instanceof HTMLElement) && (item.style.opacity = '0.5'); }, 0);
         });

         item.addEventListener('dragend', () => {
            setTimeout(() => { (item instanceof HTMLElement) && (item.style.opacity = '1'); draggedItem = null; }, 0);
         });

         item.addEventListener('dragover', (e) => {
            if (canDrop(item)) {
               e.preventDefault();
               item.classList.add('over');
            } else {
               item.classList.remove('over');
            }
         });

         item.addEventListener('dragleave', () => {
            item.classList.remove('over');
         });

         item.addEventListener('drop', (e) => {
            e.preventDefault();
            item.classList.remove('over');
            if (canDrop(item) && draggedItem) {
               const draggedContent = draggedItem.innerHTML;
               draggedItem.innerHTML = item.innerHTML;
               item.innerHTML = draggedContent;
               const newOrder = getReticuleOrder()
               const gridIsOriginal = (newOrder == gridInitialOrder)
               cargo[cargoKeys.data] = gridIsOriginal ? '' : newOrder
               btnSave.disabled = gridIsOriginal;
               btnExport.disabled = !gridIsOriginal
            }
         });
      });
   }

   initializeDragAndDrop();

});


//-------------
// == Ag Grid
const gridOptions = {
   rowSelection: 'single',
   onGridReady: (params) => {
      const firstRow = cargo ? params.api.getDisplayedRowAtIndex(cargo[cargoKeys.row_index]) : null;
      setTimeout(() => { firstRow?.setSelected(true); setActiveRow(firstRow, firstRow?.rowIndex) }, 20);
   },
   onCellFocused: (event) => {
      let row = (event.rowIndex === null) || !event.api ? null : event.api.getDisplayedRowAtIndex(event.rowIndex);
      setActiveRow(row, event.rowIndex)
   }
   , rowData: gridRows
   , columnDefs: [
      { field: colCode, flex: 1, hide: true },
      { field: colSep, flex: 1, hide: true },
      { field: colScm, flex: 1, hide: true },
      { field: colMeta[3].n, headerName: colMeta[3].h, hide: true, flex: 1 },
      { field: colMeta[4].n, headerName: colMeta[4].h, hide: false, flex: 4 },
      {
         field: colMeta[5].n, headerName: colMeta[5].h, hide: false, flex: 3,
         valueFormatter: params => new Date(params.value).toLocaleString(dateFormat),
      },
      { field: colMeta[6].n, headerName: colMeta[6].h, hide: false, flex: 2 }
   ]
}; // gridOptions


//-------------
//== Init
// @ts-ignore
const gridContainer = document.getElementById(gridID);
agGrid.createGrid(gridContainer, gridOptions);

//== eof
