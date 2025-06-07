document.addEventListener("DOMContentLoaded", () => {
    const initialized = new Set();

    document.querySelectorAll("div.editor-quill").forEach((editor) => {
        const targetId = editor.dataset.target;

        if (!targetId || initialized.has(editor.id)) return;

        const quill = new Quill(`#${editor.id}`, {
            theme: "snow",
            placeholder: "Введіть текст...",
            modules: {
                toolbar: [
                    ["bold", "italic", "underline", "strike", "code"],
                    ["clean"]
                ],
            },
        });

        console.log(targetId)

        // Найти ближайшую форму
        const formId = editor.dataset.formId;
        const form = document.getElementById(formId);
        console.log(form.id)
        if (form) {
            form.addEventListener("submit", () => {
                const input = document.querySelector(`#${targetId}`);
                console.log(input)
                if (input) {
                    console.log(quill.root.innerHTML)
                    input.value = quill.root.innerHTML;
                }
            });
        }

        initialized.add(editor.id);
    });
});
