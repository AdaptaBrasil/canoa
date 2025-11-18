// /static/js/ag-grid-helper.js
// mgd 2025-10-07

/**
 * Handles ensuring a row is visible, selected, and focused on grid ready.
 */
export const agGridReadyHandler = (params, rowIndexToFocus, setActiveRow) => {
   if (rowIndexToFocus !== undefined && rowIndexToFocus !== null) {
      setTimeout(() => {
         // A. Ensure the row is scrolled into view
         params.api.ensureIndexVisible(rowIndexToFocus);

         // B. Select the row
         params.api.selectIndex(rowIndexToFocus, false, false);

         // C. Set focus to the first cell
         const firstColKey = params.columnApi.getAllDisplayedColumns()[0].getColId();
         params.api.setFocusedCell(rowIndexToFocus, firstColKey);

         // D. Your custom active row logic
         const focusedRowNode = params.api.getDisplayedRowAtIndex(rowIndexToFocus);
         if (focusedRowNode && setActiveRow) {
            setActiveRow(focusedRowNode, rowIndexToFocus);
         }
      }, 50);
   }
};

/**
 * Handles custom logic when a cell is focused.
 */
export const agCellFocusedHandler = (event, setActiveRow) => {
   let row = (event.rowIndex === null) || !event.api ? null : event.api.getDisplayedRowAtIndex(event.rowIndex);
   if (setActiveRow) {
      setActiveRow(row, event.rowIndex);
   }
};

// eof