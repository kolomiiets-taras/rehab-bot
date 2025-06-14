async function confirmAppointment(id) {
    try {
        const response = await fetch(`/api/appointments/confirm/${id}`, {
            method: "POST"
        });

        if (!response.ok) throw new Error("Failed to confirm");

        await loadAppointments(currentPending);  // не вызывай без аргумента
        await updatePendingBadge();              // бейдж тоже обнови вручную
    } catch (error) {
        alert("Помилка при підтвердженні запису");
        console.error(error);
    }
}


async function updatePendingBadge() {
    try {
        const response = await fetch("/api/appointments/true");
        const data = await response.json();
        const badge = document.getElementById("alert-badge");

        if (data.length === 0) {
            badge.style.display = "none";
        } else {
            badge.style.display = "inline-block";
            badge.textContent = data.length > 9 ? "9+" : data.length;
        }
    } catch (err) {
        console.error("Error updating badge:", err);
    }
}

let currentPending = true;

async function loadAppointments(pending = true) {
    currentPending = pending;
    const container = document.getElementById("appointments-container");
    container.innerHTML = '<div class="text-center p-2 text-muted">Завантаження...</div>';

    try {
        const response = await fetch(`/api/appointments/${pending}`);
        const data = await response.json();

        if (data.length === 0) {
            container.innerHTML = '<div class="text-center p-2 text-muted">Немає нових запитів</div>';
            return;
        }

        container.innerHTML = "";
        data.forEach(app => {
            const createdAt = new Date(app.created_at).toLocaleString();
            container.innerHTML += `
                <li class="dropdown-item d-flex align-items-center">
                    <div class="mr-3">
                        <div class="icon-circle bg-warning">
                            <i class="fas fa-user text-white"></i>
                        </div>
                    </div>
                    <div class="mr-3">
                        <div class="small text-gray-500">${createdAt}</div>
                        <span class="font-weight-bold">${app.user_name} (${app.user_phone})</span>
                    </div>
                    ${pending === true ? `
                        <div>
                            <button class="btn btn-success btn-circle btn-sm" onclick="confirmAppointment(${app.id});">
                                <i class="fa-solid fa-check text-white"></i>
                            </button>
                        </div>` : ''}
                </li>
            `;
        });
    } catch (err) {
        container.innerHTML = '<div class="text-center p-2 text-danger">Помилка при завантаженні</div>';
        console.error("Error loading appointments:", err);
    }
}

function toggleAppointmentsView(button) {
    const newPending = !currentPending;
    loadAppointments(newPending);
    button.innerText = newPending ? "Показати оброблені" : "Показати очікуючі";
}

setInterval(() => {
    updatePendingBadge();             // всегда обновляем бейджик
    loadAppointments(currentPending); // загружаем текущий список
}, 10000);

document.addEventListener("DOMContentLoaded", () => {
    loadAppointments(true);       // по умолчанию — очікуючі
    updatePendingBadge();         // сразу отрисовать бейджик
});