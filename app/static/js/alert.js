document.addEventListener('DOMContentLoaded', function () {
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    toastElList.forEach(function (toastEl) {
        new bootstrap.Toast(toastEl, {delay: 3000}).show();
    });
});
setTimeout(function () {
    const alert = document.querySelector('.alert');
    if (alert) {
        alert.classList.remove('show');
        alert.classList.add('fade');
        alert.style.display = 'none';
    }
}, 4000);