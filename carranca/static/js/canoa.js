/* canoa's common javaScript

*/

/** @type {CanoaGlobal} */
window.Canoa = { dataModified: false, wake_up_in_ms: 6000 }

const setSleepVeil = () => {
    const sv = document.querySelector('[data-sleep-veil]');
    if (sv) {
        sv.className = 'dlg-sleep-veil';

        // download_ready cookie trick: the server Set-Cookie's this on the file response,
        // which arrives with the response headers -- well before the body finishes streaming
        // -- so polling for it hides the veil as soon as the download actually starts,
        // instead of guessing a fixed delay.
        // keep in sync with carranca/common/app_constants.py's APP_DOWNLOAD_READY_COOKIE --
        // this file is static (not Jinja-rendered), so it can't import that constant directly
        const cookieName = 'download_ready';
        const clearCookie = () => { document.cookie = `${cookieName}=; Max-Age=0; path=/`; };
        const hide = () => { sv.className = 'd-none'; };

        clearCookie(); // drop any stale cookie from a previous download before polling
        const poll = setInterval(() => {
            if (document.cookie.includes(`${cookieName}=1`)) {
                clearInterval(poll);
                clearTimeout(timeout);
                clearCookie();
                hide();
            }
        }, 300);

        // safety net in case the cookie never arrives (eg. cookies blocked,
        // a same-tab navigation, or a route that doesn't set it)
        const timeout = setTimeout(() => { clearInterval(poll); hide(); }, Canoa.wake_up_in_ms);
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
    } else if (frm.hasAttribute('data-form-close') && frm.action && Canoa.dataModified) {
        if (confirm("Perder as alterações?")) {
            Canoa.dataModified = false;
        } else {
            e.preventDefault();
        }
    }
});

/* eof */