/* canoa's common javaScript

*/

/** @type {CanoaGlobal} */
window.Canoa = { dataModified: false, }

const setSleepVeil = () => {
    const sv = document.querySelector('[data-sleep-veil]');
    if (sv) {
        sv.className = 'dlg-sleep-veil';
    }
}

window.addEventListener('beforeunload', (event) => {
    if (Canoa.dataModified) {
        event.preventDefault();
    }
});

document.addEventListener('submit', (e) => {
    const frm = e.target.closest('form');
    const btn = e.submitter;
    const isNewTab = (btn && btn.getAttribute('formtarget') === '_blank') || (frm.getAttribute('target') === '_blank');

    if (frm == null) {
        // chau
    } else if (frm.hasAttribute('data-wait-process') && frm.action && !isNewTab) {
        const route = frm.action.split('/').at(-1);
        if (!['login', 'logout', 'goto'].includes(route)) {
            setSleepVeil();
        }
    } else if (frm.hasAttribute('data-form-close') && frm.action && Canoa.dataModified ) {
        if (!confirm("Perder as alterações?")) {
            e.preventDefault();
        }
    }
});

/* eof */