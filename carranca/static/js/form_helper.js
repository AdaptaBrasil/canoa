/**
 * form_helper.js
 * version 0.1
 * 2024.11.25
 *
 * for `/layouts/form.html.j2`
 *
 * Miguel Gastelumendi -- mgd
*/


document.addEventListener('DOMContentLoaded', () => {
    const formID = "id-form-main";//"{{ formID }}";
    const form = document.getElementById(formID);
    const formOnSubmit = (event) => {
        event.preventDefault(); // Prevents form submission
        alert(form.id); // Shows the form element ID
        return false;
    };
    form.addEventListener('submit', formOnSubmit);
})

document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    forms.forEach((form) => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const specificInput = form.querySelector('#id_this_is_me');
            if (specificInput) {
                alert(`Form with ID: ${form.id} contains the specific input with ID: ${specificInput.id}`);
            } else {
                alert(`Form with ID: ${form.id} does NOT contain the specific input`);
            }
            return false;
        });
    });
});


// eof