/**
 * @preserve
 * Wizard js
 * version 1.7.0
 * 2022.12.22--29 / 2023.01.03--07,23; 05.24,25 /
 * Miguel Gastelumendi -- mgd
 */
// @ts-check
/* cSpell:locale en, pt-br */

/**
 * This callback should return true to go
 * @callback fOnNext
 * @returns {boolean}
 */

/**
 * @typedef {Object} wzdItem
 * @property {string} [bodyId = "wzdBody"] parent ID element of the buttons
 * @property {string} hint hint for the element
 * @property {boolean} [selected = false] item is selected
 * @property {string} text buttons text, if nul/undef caption is used
 * @property {string} caption display on selection
 * @property {number} id item`s ID, if informed, it is sent as a parameter
 * @property {string} [type = "success"] info type(https://getbootstrap.com/docs/5.0/components/alerts/)
 * @property {string} href address of the next page (if all items have the same one, use 'nextPage')
 * @property {string} fileName image file name and extension
 */

/**
 * @typedef {Object} wzdConfig
 * @property {Array<wzdItem>} data array of json items
 * @property {number} mode see wzdControl.mode
 * @property {fOnNext?} onNext callback on Next button
 * @property {string?} nextPage address of next page
 * @property {string?} path to wzdItem.fileName
 * @property {string?} [help] callback function to fetch help html text (use <p></p> instead of <br>)
 * @property {string?} [alignText = 'center'] buttons text alignment [center|start|end]
 * @property {boolean?} [multiSelect = false] allow selected item per group
 */

/**
 * @typedef {Object} groupItem
 * @property {string} bodyId the ID of the parent element (this is an 'index' to wzdConfig<wzdItem>.bodyId
 * @property {number} selectedItemIx If multiSelect: select button ix or -1
 */

/**
 * @typedef {Object} wzdControl
 * @property {Function} initPage
 * @property {Function} messageInfo
 * @property {Function} messageError
 * @property {fOnNext} fOnNext
 * :
 * @property {string?} nextPageHref address of next page
 *
 */

const wzdControl = {
  multiSelect: false,
  selectedItemIx: -1, // Selected item index, when multiSelect is false
  nextPageHref: "",   // Wizard page has ony one target
  /** @type {number} */
  displayMode: 0,
  /** @type {Array<groupItem>}*/
  groups: [],
  /** @type {Array<wzdItem>} */
  jsoData: [],
  /** @type {fOnNext?} */
  fOnNext: null,
  helpCallback: "", // Fetch server help address

  ge: (/** @type {string} */ sId) => /** @type{HTMLElement} */(document.getElementById(sId)),
  getBtn: (/** @type {number} */ ix) => wzdControl.ge(wzdControl.getBtnId(ix)),
  getBtnId: (/** @type {number} */ ix) => `wzdBtn${ix}`,
  getBtnHint: (/** @type {string} */ sHint) => {
    return !sHint
      ? ""  // TODO: colocar no CSS
      : `<button type="button" class="btn btnHelper" style="width: 30px; height: 30px; border-radius: 100%; align-items: center; display: inline-flex; justify-content: center;" tabindex="-1" data-bs-placement="left" data-bs-trigger="focus" data-bs-toggle="popover" data-bs-title="Ajuda" data-bs-content="${sHint}">?</button>`;
  },
  setBody: (/** @type {string} */ sId, /** @type {string} */ sBody) => (wzdControl.ge(sId).innerHTML = "" + sBody),

  getColClasses: (/** @type {string} */ sBodyId) => {
    const w = wzdControl.jsoData.filter(itm => itm.bodyId == sBodyId).length;
    const sCols =
      "row-cols-1" +
      (w > 1 ? " row-cols-sm-2" : "") +
      (w > 2 && w & 1 ? " row-cols-md-3" : "") + // ()> 2 && odd)
      (w > 3 ? " row-cols-lg-4" : "");
    return sCols;
  },

  getSelectedCount: () =>
    wzdControl.multiSelect
      ? wzdControl.groups.filter(grp => grp.selectedItemIx >= 0).length
      : wzdControl.selectedItemIx < 0 ? 0 : 1,

  getTitle: sDefault => sDefault ? sDefault : wzdControl.ge("wzdDescription").innerText,

  getGroupItemByIx: (/** @type {number} */ ix) => {
    const itm = wzdControl.jsoData[ix];
    return /** @type {groupItem} */ (wzdControl.groups.find(grp => grp.bodyId == itm.bodyId));
  },

  //@ts-ignore mdlControl is defined on modal.js
  modalReady: () => (typeof mdlControl == "object"),

  /** @private */
  showSelected: () => {
    const i = wzdControl.getSelectedCount();
    let sSelected = `Selecionado${i == 1 ? "" : "s"}: <b>`;
    if (wzdControl.multiSelect) {
      sSelected += wzdControl.groups
        .filter(grp => grp.selectedItemIx >= 0)
        .map(grp => wzdControl.jsoData[grp.selectedItemIx].caption)
        .join(", ");
    } else {
      sSelected += wzdControl.jsoData[wzdControl.selectedItemIx].caption;
    }
    wzdControl.displaySelected(sSelected + "</b>");
  },

  /** @private */
  selectItem: (/** @type {number} */ ix) => {
    let iLastSelectedItemIx;
    let grp = {};
    if (wzdControl.multiSelect) {
      grp = wzdControl.getGroupItemByIx(ix);
      iLastSelectedItemIx = grp.selectedItemIx;
    } else {
      iLastSelectedItemIx = wzdControl.selectedItemIx;
    }
    if (iLastSelectedItemIx == ix) {
      return;
    }

    let eleBtn = wzdControl.getBtn(ix);
    eleBtn.classList.remove("btnContent");
    eleBtn.classList.add("btnSelected");
    if (iLastSelectedItemIx >= 0) {
      eleBtn = wzdControl.getBtn(iLastSelectedItemIx);
      eleBtn.classList.remove("btnSelected");
      eleBtn.classList.add("btnContent");
    }
    // save
    if (wzdControl.multiSelect) {
      grp.selectedItemIx = ix;
    }
    else {
      wzdControl.selectedItemIx = ix;
    }
    wzdControl.showSelected();
  },

  /** @private */
  display: () => {
    const aBody = []; // array with the IDs of each body (parent's ids)
    const aHtml = []; // HTML for each parent body
    // Set default values
    const aSelected = [];
    wzdControl.jsoData.forEach((itm, ix) => {
      if (!itm.bodyId) itm.bodyId = "wzdBody";
      if (!itm.type) itm.type = "success";

      //@ts-ignore cast error: but as 'itm.selected' is not bool => try as string
      if (!((typeof itm.selected == typeof true) ? itm.selected : (parseInt('0' + (/** @type {string} */(itm.selected) || '')) ? true : false))) {
        itm.selected = false;
      } else if (wzdControl.multiSelect ? /* one by group */(aSelected.indexOf(itm.bodyId) < 0) : /* one per page */ (aSelected.length == 0)) {
        itm.selected = true;
        aSelected.push(itm.bodyId);
      } else /* just one item can be selected (per group or page)*/ {
        itm.selected = false;
      }
    });
    const _getBodyIx = (sBodyId, sOpenDiv) => {
      let id = aBody.indexOf(sBodyId);
      if (id < 0) {
        id = aBody.push(sBodyId) - 1;
        aHtml.push(sOpenDiv);
        wzdControl.groups.push({ bodyId: sBodyId, selectedItemIx: -1 });
      }
      return id;
    };
    const _selectItem = (/** @type {number} */ix) => {
      if (wzdControl.multiSelect) {
        const grp = wzdControl.getGroupItemByIx(ix);
        grp.selectedItemIx = ix;
      } else {
        wzdControl.selectedItemIx = ix;
      };
      wzdControl.showSelected();
    };
    let bodyIx;
    let sAlign = "text-" + wzdControl.alignText;
    switch (wzdControl.displayMode) {
      case wzdControl.mode.CUSTOM:
        return;
      case wzdControl.mode.BUTTONS:
        wzdControl.jsoData.forEach((itm, ix) => {
          bodyIx = _getBodyIx(itm.bodyId, '<div class="d-grid gap-4">');
          if (itm.selected) { _selectItem(ix); }

          aHtml[bodyIx] +=
            `<div>
            ${wzdControl.getBtnHint(itm.hint)}
            <button id="${wzdControl.getBtnId(ix)}"
              class="btn ${(itm.selected ? 'btnSelected' : 'btnContent')} ${sAlign}"; style="width: 50%;" type="button" onclick="wzdControl.selectItem(${ix})">` +
            (itm.text ? itm.text : itm.caption) +
            "</button>" +
            "</div>";
        });
        break;
      case wzdControl.mode.INFO:
        wzdControl.jsoData.forEach((itm, ix) => {
          bodyIx = _getBodyIx(itm.bodyId, `<div class="d-grid gap-2 ${sAlign}">`);
          aHtml[bodyIx] +=
            `<div id="${wzdControl.getBtnId(ix)}" class="alert alert-${itm.type}">` +
            (itm.caption ? `<h4 class="alert-heading">${itm.caption}</h4>${itm.text ? "<hr>" : ""}` : "") +
            (itm.text || "") +
            "</div>";
        });
        break;
      case wzdControl.mode.IMAGES:
        wzdControl.jsoData.forEach((itm, ix) => {
          bodyIx = _getBodyIx(itm.bodyId, `<div class="row ${wzdControl.getColClasses(/** @type {string} */(itm.bodyId))}">`);
          if (itm.selected) { _selectItem(ix); }

          let onClick = `onclick="wzdControl.selectItem(${ix})`;
          aHtml[bodyIx] +=
            `<div class="col ${sAlign} mb-3">` +
            `<button id=${wzdControl.getBtnId(ix)} class="btn bg-gradient ${(itm.selected ? 'btnSelected' : 'btnContent')}" type="button" ${onClick}">` +
            `<a ${onClick}"> <img src="${wzdControl.path}${itm.fileName}" alt="${itm.fileName ? itm.fileName : "Imagem não disponível"}"></a>` +
            "</button>" +
            '<span class=""><i style="font-size: 23px; margin: 10px; color: white; cursor: pointer;" class="far fa-question-circle"></i></span>' +
            "</div>";
        });
        break;
      default:
        wzdControl.jsoData.forEach(itm => { _getBodyIx(itm.bodyId, "<div>"); });
        break;
    }
    aBody.forEach((sBodyId, i) =>
      wzdControl.setBody(sBodyId, aHtml[i] + "</div>")
    );
  },

  /** @private */
  selectionReady: o => {
    let i;
    const k = wzdControl.groups.length;
    if (!wzdControl.multiSelect && (wzdControl.displayMode != wzdControl.mode.INFO)) {
      o.msg = "Por favor, selecione uma das opções.";
      return wzdControl.selectedItemIx >= 0;
    } else if (!wzdControl.nextPageHref) {
      o.msg = `Não está definido o próximo passo para seleção múltipla.`;
    } else if (k == (i = wzdControl.getSelectedCount())) {
      return true;
    } else if (k == 1) {
      // Um grupo somente
      o.msg = `Por favor, selecione uma das opções do grupo.`;
    } else {
      o.msg = `Por favor, selecione uma opção de cada um dos ${k} grupos`;
      const f = k - i;
      o.msg += i == 0 ? "." : ` (falta${f == 1 ? " um" : `m ${f}`}).`;
    }
    return false;
  },

  /** @protected */
  gotoNextPage: () => {
    let sHref = "";
    let jsBtn;
    let o = { msg: "" };
    if (wzdControl.fOnNext && !wzdControl.fOnNext()) {
      // Not this time 8-|
      // Mauro 08/01/23
    } else if ((wzdControl.displayMode == wzdControl.mode.CUSTOM) || (wzdControl.displayMode == wzdControl.mode.INFO)) {
      sHref = wzdControl.nextPageHref;
    } else if (wzdControl.jsoData.length == 0) {
      wzdControl.messageError(`Não exitem items para selecionar.`);
    } else if (!wzdControl.selectionReady(o)) {
      wzdControl.messageInfo(o.msg);
    } else if (wzdControl.multiSelect) {
      const sIds = wzdControl.groups
        .map(grp => wzdControl.jsoData[grp.selectedItemIx].id)
        .join("-");
      sHref = `${wzdControl.nextPageHref}?id=${sIds}`;
    } else if ((jsBtn = wzdControl.jsoData[wzdControl.selectedItemIx]).href) {
      sHref = jsBtn.href;
    } else if (!wzdControl.nextPageHref) {
      wzdControl.messageError(
        `Não está definido o próximo passo de '${jsBtn.caption}'.`
      );
    }
    else if (jsBtn.id) {
      sHref = `${wzdControl.nextPageHref}?id=${jsBtn.id}`;
    } else {
      sHref = jsBtn.href || wzdControl.nextPageHref;
    }
    if (sHref)
      setTimeout(() => {
        window.location.href = sHref;
      }, 0);
    console.log("Button details:");

  },

  /** @protected */
  displayHelp: () => {
    wzdControl.fetchObject(
      wzdControl.helpCallback,
      oData => {
        wzdControl.modalReady() // @ts-ignore mdlControl
          ? mdlControl.displayHelp(oData.text, wzdControl.getTitle(oData.title))
          : wzdControl.messageInfo(
            "O recurso de exibição de Ajuda, não está disponível no momento."
          );
      },
      "No momento, não temos ajuda para este tópico"
    );
  },

  /** @public */
  goBack: () => {
    window.history.back();
  },

  /**
   * Return true if the f is a function
   * @param {function} f
   * @returns {boolean}
   * @public
   */
  paramIsFunction: f => typeof f === "function",

  /** @public */
  messageInfo: (sMsg, sTitle) => {
    if (wzdControl.modalReady()) {
      // @ts-ignore mdlControl
      mdlControl.messageInfo(sMsg, wzdControl.getTitle(sTitle));
    } else {
      alert(sMsg);
    }
  },

  /** @public */
  messageError: (sMsg, sTitle, sError, fOnError) => {
    if (fOnError) {
      fOnError();
    }
    if (wzdControl.modalReady()) {
      // @ts-ignore mdlControl
      mdlControl.messageError(sMsg, wzdControl.getTitle(sTitle), sError);
    } else {
      wzdControl.messageInfo(
        sMsg + "\n\n" + sError,
        wzdControl.getTitle(sTitle)
      );
    }
  },

  /**
   * Return the text of the selected option of the param
   * @param {HTMLSelectElement} eleSelect
   * @returns {string}
   * @public
   */
  getSelectedTextFrom: eleSelect => {
    let sText = "";
    if (eleSelect && eleSelect.selectedIndex >= 0) {
      sText = eleSelect.options[eleSelect.selectedIndex].text;
    }
    return sText;
  },

  /**
   * Display HTML text of selected item
   * @param {string} sHtml
   * @public
   */
  displaySelected: sHtml => {
    const eleUsDisplay = wzdControl.ge("wzdSelectedItem");
    eleUsDisplay.innerHTML = "" + sHtml;
    if (sHtml) {
      eleUsDisplay.classList.remove("visually-hidden");
    } else {
      eleUsDisplay.classList.add("visually-hidden");
    }
  },

  /**
   * @readonly
   * @enum {number} Wizard item's display mode
   * @public
   */
  mode: { BUTTONS: 1, IMAGES: 2, INFO: 3, CUSTOM: 4 },

  /**
   * Fetch jSon object from the server
   * @param {string} sCallback
   * @param {function( object )} fSuccess
   * @param {function | string} fFailure callback function | error string
   * @param {function( object )} [fAlways] TODO
   * @param {Object} options = { data: {}, type: 'text'|'json'}
   * @public
   */

  fetchObject: async (sCallback, fSuccess, fFailure, fAlways, options = {}) => {
    const typText = "text";
    const typJson = "json";
    const _f = (f, p) => (wzdControl.paramIsFunction(f) ? f(p) || true : false);
    const _e = r =>
      wzdControl.messageError(fFailure, "", `Status: ${r.status}].`);
    await fetch(sCallback, options.data || {}).then(rsp => {
      if (!rsp.ok) {
        return _e(rsp);
      }
      const _get = async () => {
        try {
          const jsoData = await ((options.type || typJson) == typJson ? rsp.json() : rsp.text());
          if (rsp.ok) {
            _f(fSuccess, jsoData);
          } else {
            _e(rsp);
          }
        } catch (e) {
          wzdControl.messageError("Houve um erro ao recuperar as informações recebidas.", "", e.message);
        }
      };
      _get();
    });
  },

  /**
   * Initialize wizard's page
   * @param {wzdConfig} jsonConfig
   * @public
   */
  initPage: jsonConfig => {
    wzdControl.jsoData = jsonConfig.data || [];
    wzdControl.displayMode = jsonConfig.mode;
    wzdControl.fOnNext = jsonConfig.onNext || null;
    wzdControl.nextPageHref = (jsonConfig.nextPage || "").trim();
    wzdControl.helpCallback = jsonConfig.help || "";
    wzdControl.path = (jsonConfig.path || "../../static/assets/img/wizard/").trim();
    wzdControl.multiSelect = jsonConfig.multiSelect || false;
    wzdControl.alignText = jsonConfig.alignText || (jsonConfig.mode == wzdControl.mode.INFO ? "left" : "center");
    if (!wzdControl.path.endsWith("/")) wzdControl.path += "/";
    setTimeout(() => wzdControl.display(), 0);
    // don't use try catch, if an error occurs, better leave button disabled
    /** @type {HTMLButtonElement} */ (wzdControl.ge("wzdBtnOk")).disabled = false;
    /** @type {HTMLButtonElement} */ (wzdControl.ge("wzdBtnHelp")).disabled = (wzdControl.helpCallback == "");
  },
};
//{# eof #}
