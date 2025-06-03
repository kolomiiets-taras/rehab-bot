// static/js/edit-complex-modal.js

// Обвязка: для каждого модального окна с классом .edit-complex-modal
;(function () {
  // ждём, пока DOM загрузится
  document.addEventListener('DOMContentLoaded', () => {
    // обрабатываем каждую модалку редактирования
    document.querySelectorAll('.edit-complex-modal').forEach(modalEl => {
      const complexId = modalEl.dataset.complexId;
      const selectEl = $(modalEl).find('.exercise-select');
      const selectedListEl = $(modalEl).find('.selected-exercises');
      const hiddenInput = $(modalEl).find('.exercises-json');
      let selectedExercises = [];

      // инициализация Select2 на нужном селекте
      selectEl.select2({
        placeholder: 'Почніть вводити назву вправи',
        dropdownParent: modalEl
      });

      // При открытии модалки: подгружаем список всех упражнений (один раз) и инициализируем state
      $(modalEl).on('shown.bs.modal', async () => {
        // подгружаем опции, если их ещё нет
        if (!selectEl.children().length) {
          try {
            const res = await fetch('/api/exercises');
            const data = await res.json();
            data.forEach(ex => {
              selectEl.append(new Option(ex.title, ex.id, false, false));
            });
          } catch (err) {
            console.error('Не вдалося завантажити вправи:', err);
          }
        }

        // читаем текущее значение JSON из скрытого поля
        try {
          const init = JSON.parse(hiddenInput.val() || '[]');
          init.forEach(item => {
            // ищем заголовок в уже отрендеренных <li>
            const title = selectedListEl
              .find(`li[data-id="${item.id}"]`)
              .clone()
              .children()
              .remove()
              .end()
              .text()
              .trim();
            selectedExercises.push({ id: item.id, title });
          });
        } catch (_) { /* ignore */ }

        updateSelectedView();
      });

      // Когда пользователь выбирает опцию в Select2
      selectEl.on('select2:select', e => {
        const { id, text } = e.params.data;
        if (!selectedExercises.find(ex => ex.id == id)) {
          selectedExercises.push({ id, title: text });
          updateSelectedView();
        }
        // сброс выбора
        selectEl.val(null).trigger('change');
      });

      // Удаление из списка при клике на крестик
      selectedListEl.on('click', '.remove-btn', function () {
        const li = $(this).closest('li');
        const id = li.data('id');
        selectedExercises = selectedExercises.filter(ex => ex.id != id);
        updateSelectedView();
      });

      // Подключаем drag&drop через Sortable.js
      new Sortable(selectedListEl[0], {
        animation: 150,
        onEnd: function () {
          const reordered = [];
          selectedListEl.children('li').each(function () {
            const id = $(this).data('id');
            const ex = selectedExercises.find(e => e.id == id);
            if (ex) reordered.push(ex);
          });
          selectedExercises = reordered;
          updateSelectedView();
        }
      });

      // Перерисовка списка и обновление hidden-input
      function updateSelectedView() {
        selectedListEl.empty();
        selectedExercises.forEach((ex, idx) => {
          selectedListEl.append(`
            <li
              class="list-group-item d-flex justify-content-between align-items-center"
              data-id="${ex.id}"
            >
              ${ex.title}
              <button
                type="button"
                class="btn btn-sm btn-danger remove-btn">&times;
              </button>
            </li>
          `);
        });

        // Подготавливаем JSON: [{id:…,position:…},…]
        const payload = selectedExercises.map((ex, i) => ({
          id: ex.id,
          position: i + 1
        }));
        hiddenInput.val(JSON.stringify(payload));
      }
    });
  });
})();
