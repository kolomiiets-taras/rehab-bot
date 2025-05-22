// static/js/edit-course-modal.js
$(function(){
  const loaded = {};

  // Підключаємося до всіх модалок з класом .edit-course-modal
  $('body').on('shown.bs.modal', '.edit-course-modal', async function(){
    const modal     = $(this);
    const courseId  = modal.data('course-id');
    if (loaded[courseId]) return;  // вже ініціалізовано

    // Елементи форми всередині цієї модалки
    const $select = modal.find('#item-select');
    const $list   = modal.find('#selected-items');
    const $hidden = modal.find('#items-json');

    // Забираємо вже наявні елементи з data-items
    // grab the raw JSON string from the attribute:
    const itemsJson = modal.attr('data-items') || '[]';

    let selected;
    try {
      selected = JSON.parse(itemsJson);
    } catch(e) {
      console.error('Invalid data-items JSON:', e, itemsJson);
      selected = [];
    }

    // 1) Ініціалізуємо Select2 у контексті цієї модалки
    $select.select2({
      placeholder: 'Почніть вводити назву…',
      dropdownParent: modal
    });

    // 2) Завантажуємо вправи та комплекси з API
    try {
      const [exRes, cxRes] = await Promise.all([
        fetch('/api/exercises').then(r=>r.json()),
        fetch('/api/complexes').then(r=>r.json())
      ]);

      const exGroup = $('<optgroup label="Вправи">');
      exRes.forEach(ex=>{
        exGroup.append(new Option(ex.title, `exercise_${ex.id}`));
      });

      const cxGroup = $('<optgroup label="Комплекси">');
      cxRes.forEach(cx=>{
        cxGroup.append(new Option(cx.name, `complex_${cx.id}`));
      });

      $select.append(exGroup).append(cxGroup).trigger('change');
    } catch(err) {
      console.error('Не вдалося завантажити списки:', err);
    }

    // 3) Функція, що рендерить пул вибраних елементів
    function renderSelected(){
      $list.empty();
      selected.forEach(item => {
        $list.append(`
          <li class="list-group-item d-flex justify-content-between align-items-center"
              data-type="${item.type}" data-id="${item.id}">
            <span>${item.title} <small class="text-muted">[${item.type}]</small></span>
            <button type="button" class="btn btn-sm btn-danger remove-btn">&times;</button>
          </li>
        `);
      });
      // Оновлюємо hidden JSON поле
      const payload = selected.map((e,i)=>({
        type: e.type,
        id: e.id,
        position: i+1
      }));
      $hidden.val(JSON.stringify(payload));
    }

    // 4) Відмалювати початковий стан
    renderSelected();

    // 5) Обробник вибору у Select2
    $select.on('select2:select', function(e){
      const [type, idStr] = e.params.data.id.split('_');
      const id            = parseInt(idStr, 10);
      const title         = e.params.data.text;
      if (!selected.find(x=>x.type===type && x.id===id)) {
        selected.push({type,id,title});
        renderSelected();
      }
      // Очищаємо вибір у Select2
      $select.val(null).trigger('change');
    });

    // 6) Видалення з пулу
    $list.on('click', '.remove-btn', function(){
      const $li = $(this).closest('li');
      const type = $li.data('type');
      const id   = $li.data('id');
      selected = selected.filter(x=>!(x.type===type && x.id===id));
      renderSelected();
    });

    // 7) Drag & drop — оновлюємо порядок
    Sortable.create($list[0], {
      animation: 150,
      onEnd: () => {
        const reordered = [];
        $list.find('li').each(function(){
          const li = $(this);
          const type = li.data('type');
          const id   = li.data('id');
          const obj  = selected.find(x=>x.type===type && x.id===id);
          if (obj) reordered.push(obj);
        });
        selected = reordered;
        renderSelected();
      }
    });

    loaded[courseId] = true;
  });
});
