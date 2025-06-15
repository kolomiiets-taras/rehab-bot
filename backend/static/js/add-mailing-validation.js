function validateDaysSelected() {
    const checkboxes = document.querySelectorAll('input[name="mailing_days"]:checked');
    const endDateInput = document.querySelector('#end-date');

    if (checkboxes.length === 0) {
        alert("Будь ласка, оберіть хоча б один день для розсилки.");
        return false;
    }

    if (!endDateInput || !endDateInput.value) {
        alert("Будь ласка, оберіть дату завершення курсу.");
        endDateInput.focus();
        return false;
    }

    return true;
}

$(document).ready(function () {
    $('#user-select').select2({
        placeholder: 'Виберіть пацієнтів…'
    });
});
$(document).ready(function () {
    $('#course-select').select2({
        placeholder: 'Виберіть курс…',
        allowClear: true,
        theme: 'bootstrap4'
    });
});
$(document).ready(function () {
    $('#mailing-time').select2({
        placeholder: 'Виберіть час…',
        theme: 'bootstrap4'
    });
});