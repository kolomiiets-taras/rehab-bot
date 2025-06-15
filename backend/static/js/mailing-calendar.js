let flatpickrInstance = null;
    function getSelectedWeekdays() {
        const checkboxes = document.querySelectorAll('input[name="mailing_days"]:checked');
        return Array.from(checkboxes).map(cb => parseInt(cb.value)); // 1 (Пн) – 7 (Нд)
    }

    function setupFlatpickr() {
        const weekdays = getSelectedWeekdays(); // [2, 4] наприклад

        if (flatpickrInstance) {
            flatpickrInstance.destroy();
        }

        flatpickrInstance = flatpickr("#end-date", {
            minDate: "today",
            dateFormat: "Y-m-d",
            disable: [
                function (date) {
                    // JS: Sunday = 0, Saturday = 6
                    const jsDay = date.getDay(); // 0 - 6
                    const ourIndex = jsDay === 0 ? 7 : jsDay; // Sunday = 7
                    return !weekdays.includes(ourIndex); // disable якщо не входить у вибрані
                }
            ]
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        setupFlatpickr();

        document.querySelectorAll('input[name="mailing_days"]').forEach(cb => {
            cb.addEventListener("change", setupFlatpickr);
        });
    });
