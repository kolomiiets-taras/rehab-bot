async function confirmAppointment(id) {
    try {
        const response = await fetch(`/api/appointments/confirm/${id}`, {
            method: "POST"
        });

        if (!response.ok) throw new Error("Failed to confirm");
        await loadAppointments();  // Перезавантаж список
    } catch (error) {
        alert("Помилка при підтвердженні запису");
        console.error(error);
    }
}

async function loadAppointments() {
    const container = document.getElementById("appointments-container");
    container.innerHTML = '<div class="text-center p-2 text-muted">Завантаження...</div>';
    const badge = document.getElementById("alert-badge");

    try {
        const response = await fetch("/api/appointments");
        const data = await response.json();

        if (data.length === 0) {
            badge.style.display = "none";
            container.innerHTML = '<div class="text-center p-2 text-muted">Немає нових запитів</div>';
            return;
        }

        badge.style.display = "inline-block";
        badge.textContent = data.length > 9 ? "9+" : data.length;

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
                <div>
                    <button class="btn btn-success btn-circle btn-sm" onclick="confirmAppointment(${app.id})">
                        <i class="fa-solid fa-check text-white"></i>
                    </button>
                </div>
            </li>
        `;
        });
    } catch (err) {
        container.innerHTML = '<div class="text-center p-2 text-danger">Помилка при завантаженні</div>';
        console.error("Error loading appointments:", err);
        badge.style.display = "none";
    }
}

// Автоматичне оновлення кожні 10 секунд
setInterval(loadAppointments, 10000);

// Завантаження при відкритті
document.getElementById("alertsDropdown").addEventListener("click", loadAppointments);
loadAppointments();