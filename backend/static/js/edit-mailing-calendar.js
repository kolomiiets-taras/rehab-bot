function getSelectedDays(checkboxes) {
    return Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => parseInt(cb.value));
}

// при открытии модалки
$(document).on('shown.bs.modal', function (e) {
    const modal = e.target;
    const dateInput = modal.querySelector('input.end-date');
    const checkboxes = modal.querySelectorAll('input[name="mailing_days"]');

    if (!dateInput) return;

    // удалим предыдущий flatpickr, если был
    if (dateInput._flatpickr) {
        dateInput._flatpickr.destroy();
    }

    const getDisableFn = () => {
        return [
            function (date) {
                const selectedDays = getSelectedDays(checkboxes);
                const jsDay = date.getDay(); // 0-6
                const ourDay = jsDay === 0 ? 7 : jsDay; // 1-7
                return !selectedDays.includes(ourDay);
            }
        ];
    };

    const fp = flatpickr(dateInput, {
        minDate: "today",
        dateFormat: "Y-m-d",
        disable: getDisableFn()
    });

    document.querySelectorAll('form[action^="/mailing/edit/"]').forEach(form => {
        form.addEventListener("submit", function (e) {
            if (!dateInput.value) {
                e.preventDefault();
                alert("Будь ласка, оберіть нову дату завершення курсу.");
                dateInput.focus();
            }
        });
    });

    checkboxes.forEach(cb => {
        cb.addEventListener("change", () => {
            dateInput.value = "";
            fp.setDate(null);
            fp.set('disable', getDisableFn());
        });
    });
});