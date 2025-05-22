$(document).ready(function () {
    $('#dataTable').DataTable({
        language: {
            search: "Пошук:",
            lengthMenu: "Показати _MENU_ записів",
            info: "Показано _START_ до _END_ із _TOTAL_ записів",
            paginate: {
                first: "Перша",
                last: "Остання",
                next: "Наступна",
                previous: "Попередня"
            },
            zeroRecords: "Нічого не знайдено"
        }
    });
});