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

    if (frm == null) {
        // chau
    } else if (frm.hasAttribute('data-wait-process') && frm.action) {
        const route = frm.action.split('/').at(-1);
        if (!['login', 'goto', 'logout'].includes(route)) {
            setSleepVeil();
        }
    } else if (frm.hasAttribute('data-form-close') && frm.action && Canoa.dataModified) {
        if (!confirm("Perder as alterações?")) {
            e.preventDefault();
        }
    }
});

/* eof */