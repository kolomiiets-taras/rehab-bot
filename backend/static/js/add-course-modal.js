// поводимо весь код у своєму файлі
$(function(){
  const $accordion = $('#collapseCard');
  const $modal    = $('#addCourseModal');
  const $select   = $('#item-select');
  const $list     = $('#selected-items');
  const $hidden   = $('#items-json');
  let selected = [];
  let loaded   = false;

  function renderSelected() {
    $list.empty();
    selected.forEach((e,i) => {
      $list.append(`
        <li class="list-group-item d-flex justify-content-between align-items-center"
            data-type="${e.type}" data-id="${e.id}">
          <span>${e.title} <small class="text-muted">[${e.type}]</small></span>
          <button type="button" class="btn btn-sm btn-danger remove-btn">&times;</button>
        </li>
      `);
    });
    $hidden.val(JSON.stringify(
      selected.map((e,i)=>({type:e.type, id:e.id, position:i+1}))
    ));
  }


  async function runScriptOnceConditionsMet(parent) {
    $select.select2({
        placeholder: 'Почніть вводити назву…',
        dropdownParent: parent
    });

    if (loaded) return;
    try {
      const [exRes, cxRes] = await Promise.all([
        fetch('/api/exercises').then(r=>r.json()),
        fetch('/api/complexes').then(r=>r.json())
      ]);

      const exGroup = $('<optgroup label="Вправи">');
      exRes.forEach(ex=>{
        exGroup.append(new Option(ex.title, `exercise_${ex.id}`));
      });
      $select.append(exGroup);

      const cxGroup = $('<optgroup label="Комплекси">');
      cxRes.forEach(cx=>{
        cxGroup.append(new Option(cx.name, `complex_${cx.id}`));
      });
      $select.append(cxGroup);

      loaded = true;
      $select.trigger('change');
    } catch(err) {
      console.error('Не вдалося завантажити дані:', err);
    }
    // 3) Додавання в пул
  $select.on('select2:select', e=>{
    const [type, id] = e.params.data.id.split('_');
    const title      = e.params.data.text;
    if (!selected.find(x=>x.type===type&&x.id==id)) {
      selected.push({type, id: +id, title});
      renderSelected();
    }
    $select.val(null).trigger('change');
  });

  // 4) Видалення
  $list.on('click', '.remove-btn', function(){
    const $li = $(this).closest('li');
    const t   = $li.data('type'), i = $li.data('id');
    selected = selected.filter(x=>!(x.type===t && x.id==i));
    renderSelected();
  });

  // 5) Перетягування
  Sortable.create($list[0], {
    animation: 150,
    onEnd: ()=>{
      const reordered = [];
      $list.find('li').each(function(){
        const t = $(this).data('type'), i = $(this).data('id');
        const obj = selected.find(x=>x.type===t&&x.id==i);
        if (obj) reordered.push(obj);
      });
      selected = reordered;
      renderSelected();
    }
  });
}

  // 2) При відкритті — завантажуємо вправи й комплекси лише один раз
  $modal.on('shown.bs.modal', async ()=>{
    await runScriptOnceConditionsMet($modal);
  });

  $accordion.on('shown.bs.collapse', async () => {
    await runScriptOnceConditionsMet($accordion);
  });

});
