/**
 * @preserve
 * sep_validate.js
 * version 0.2
 * 2026.07.28 -- 2026.11.16
 * Miguel Gastelumendi -- mgd
 *
 * The grid is built by CanoaAgGrid (canoa_ag_grid.js, loaded before this file);
 * here is only what is specific of this page: the [Revalidar] rule and the two cell classes.
*/
// @ts-check
/* cSpell:locale en pt-br
 */
/// <reference path="./ts-check.js" />

// == Ag Grid (single-row selection feeds [Validar Um], posting the row's `id` -- the
// user_data_files.id of the SEP's last file -- as `udf_id`; [Validar Todos] needs no
// selection and still POSTs to the under-development stub in sep_validate.py, see #61)

const selectedUdfIdInput = /** @type {HTMLInputElement} */ (document.getElementById('selected-code'));
const btnValidateOne = /** @type {HTMLButtonElement} */ (document.getElementById('btn-validate-one-id'));

/** @param {any} event */
const onSelectionChanged = event => {
    // [Revalidar] only applies to items validated by another validator version than the current one.
    // Items validated with the current version are not revalidated (same file + same validator = same result),
    // so the button stays disabled for them; the future [Revalidar todos] will skip them too.
    // Without the current version no item qualifies: sep_validate.py marks none (is_other_validator_version).
    const selected = event.api.getSelectedRows()[0];
    const row = selected?.is_other_validator_version ? selected : undefined;
    selectedUdfIdInput.value = row ? row.id : '';
    btnValidateOne.disabled = !row;
};

// "just processed today" signal: same limegreen text canoa.css's .grid-item-changed already
// uses elsewhere in the app, reused here rather than inventing a new highlight class.
/** @param {Date} value */
const isToday = value => {
    const today = new Date();
    return value.getFullYear() === today.getFullYear()
        && value.getMonth() === today.getMonth()
        && value.getDate() === today.getDate();
};

/** @param {any} params */
const isChangedToday = params => params.value && isToday(new Date(params.value));

// validator_version: "attention" when the file was validated by another validator version than the
// current one (a hidden column, set by sep_validate.py)
/** @param {any} params */
const isOtherValidatorVersion = params => !!params.data?.is_other_validator_version;

//-------------
//== Init
// Widths: only the variable-length text columns flex. uploaded_at/validator_version/validated_at have a content
// (eg "2026-07-28") much shorter than their headers: sized to the content, the header wraps onto two lines.
// report_errors/report_warns: the header is the widest thing the column shows, sized from it.
const { api } = CanoaAgGrid.create(Canoa.grid, {
    columns: {
        sep_fullname: { flex: 2 },
        manager_name: { flex: 1 },
        uploaded_at: { kind: 'iso-date', width: '10rem', wrap: true },
        validated_at: {
            kind: 'iso-datetime', width: '16rem', wrap: true,
            colDef: { cellClassRules: { 'grid-item-changed': isChangedToday } },
        },
        validator_version: {
            width: '10rem', wrap: true,
            colDef: { cellClassRules: { 'grid-item-attention': isOtherValidatorVersion } },
        },
        report_errors: { kind: 'int', width: 'header' },
        report_warns: { kind: 'int', width: 'header' },
    },
    gridOptions: { onSelectionChanged },
});
//== eof
