/**
 * @preserve
 * ts-check.js
 * 2024.10.25
 * Miguel Gastelumendi -- mgd
 *
 * A dummy variable declarations files for @ts-check
 * As an example, see sep_mgmt.js
*/
// cSpell:ignore Rprt
// @ts-check
/** @type {string} */
var gridID;
/** @type {string} */
var iconID;
/** @type {string} */
var formID;
/** @type {string} */
var respID;
/** @type {string} */
var itemNone;
// Grid
/** @type {string} */
var dateFormat;
/** @type {string} */
var colIconUrl;
/** @type {string} */
var colUserNew;
/** @type {string} */
var colUserCurr;
/** @type {string} */
var colCode;
/** @type {string} */
var colSep;
/** @type {string} */
var colScm;
/** @type {string} */
var gridInitialOrder;

/** @type {String[]} */
var userList;

/** @type {JSON} */
var gridRows;

/** @type {HTMLScriptElement} */
var jsData;

/** @type {HTMLImageElement} */
var icon_;

/** @type {HTMLButtonElement} */
var btnGridSubmit;
/** @type {HTMLButtonElement} */
var btnSave;
/** @type {HTMLButtonElement} */
var btnExport;

/** @type {Object} */
var gridContainer;

/** @type {Object} */
var params;

/**
 * @typedef {Object} ColMetaItem
 * @property {string} n
 * @property {string} h
*/

/** @type {ColMetaItem[]} */
var colMeta;

/**
 * @typedef {Object} CanoaGlobal
 * @property {boolean} dataModified
*/
/** @type {CanoaGlobal}
 * Defined in carranca\templates\layouts\dialog.html.j2 */
var Canoa;


/**
 * @typedef {Object} AgGrid
 * @property {string} action
 * @property {string} cargo
 * @property {Function} createGrid
*/

/**
 * @typedef {Object.<string, string>} Cargo
 */
/** @type {Cargo} */
var cargo;

/** @type {AgGrid} */
var agGrid

const cargoKeys = {
    actions: "actions"
    , data: "data"
    , index: "index"
    , code: "code"
    , none: "none"
};


// received_files_mgmt.js
const isPower = /** @type {bool} */ false;

/** @returns {HTMLButtonElement[]} */
var defButtons = () => [];
var getGridOrder = () => /** @type {string} */ '';

/**
 * Lives in <file>.j2 |
 * Prepares the submit cargo.
 * @param {string} r - active Row
 * @param {number} [i=null] - The Index of the active row
 */
var setActiveRow = (r, i) => { }
/* eof */
