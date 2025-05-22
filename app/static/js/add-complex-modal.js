$(document).ready(function () {
    // Ініціалізуємо Select2 у межах модалки
    $('#exercise-select').select2({
        placeholder: 'Почніть вводити назву вправи',
        dropdownParent: $('#addComplexModal')
    });

    const selectedExercises = [];
    const $selectedList = $('#selected-exercises');
    const $hiddenInput = $('#exercises-json');

    // Завантажуємо список вправ через API при першому відкритті модалки
    $('#addComplexModal').on('shown.bs.modal', async function () {
        if (!$('#exercise-select option').length) {
            try {
                const res = await fetch('/api/exercises');
                const data = await res.json();
                data.forEach(ex => {
                    $('#exercise-select').append(new Option(ex.title, ex.id, false, false));
                });
            } catch (err) {
                console.error('Не вдалося завантажити вправи:', err);
            }
        }
    });

    // Додаємо вправу у список обраних
    $('#exercise-select').on('select2:select', function (e) {
        const {id, text} = e.params.data;
        if (!selectedExercises.find(x => x.id == id)) {
            selectedExercises.push({id: Number(id), title: text});
            renderSelected();
        }
        // Очищаємо вибір, щоб можна було шукати наступну
        $('#exercise-select').val(null).trigger('change');
    });

    // Видалення з списку обраних
    $selectedList.on('click', '.remove-btn', function () {
        const id = $(this).closest('li').data('id');
        const idx = selectedExercises.findIndex(x => x.id == id);
        if (idx !== -1) {
            selectedExercises.splice(idx, 1);
            renderSelected();
        }
    });

    // Підтримка drag’n’drop через Sortable.js
    new Sortable($selectedList[0], {
        animation: 150,
        onEnd: () => {
            // Після перетягування заново збираємо порядок
            const reordered = [];
            $selectedList.children('li').each(function () {
                const id = $(this).data('id');
                const ex = selectedExercises.find(x => x.id == id);
                if (ex) reordered.push(ex);
            });
            selectedExercises.splice(0, selectedExercises.length, ...reordered);
            renderSelected();
        }
    });

    // Функція рендеру списку і оновлення схованого поля
    function renderSelected() {
        $selectedList.empty();
        selectedExercises.forEach(ex => {
            $selectedList.append(`
                <li class="list-group-item d-flex justify-content-between align-items-center" data-id="${ex.id}">
                  ${ex.title}
                  <button type="button" class="btn btn-sm btn-danger remove-btn">&times;</button>
                </li>
              `);
        });
        // Записуємо JSON масиву {id,position} у приховане поле
        $hiddenInput.val(JSON.stringify(
            selectedExercises.map((e, i) => ({id: e.id, position: i + 1}))
        ));
    }
});