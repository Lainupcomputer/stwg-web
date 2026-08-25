const userList = document.getElementById("userList");

let currentEditUserId = null;
let allUsers = [];


// ============================================================
// HILFSFUNKTIONEN
// ============================================================

function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function getStatusText(status) {

    const statuses = {
        active: "🟢 Aktiv",
        away7: "🟡 7 Tage abwesend",
        away14: "🟠 14 Tage abwesend",
        vacation: "🔵 Urlaub"
    };

    return statuses[status] || "⚫ Unbekannt";
}


function formatOnlineTime(minutes) {

    if (!minutes) {
        return "0.0h";
    }

    return `${(minutes / 60).toFixed(1)}h`;
}


function getFilteredUsers() {

    const searchInput =
        document.getElementById("searchInput");

    const filterSelect =
        document.getElementById("filterSelect");


    const searchTerm =
        searchInput
            ? searchInput.value.toLowerCase().trim()
            : "";


    const filter =
        filterSelect
            ? filterSelect.value
            : "all";


    return allUsers.filter(user => {

        const username =
            (user.username || "").toLowerCase();

        const discordId =
            String(user.user_id || "");


        const matchesSearch =
            username.includes(searchTerm) ||
            discordId.includes(searchTerm);


        let matchesFilter = true;


        switch (filter) {

            case "comments":

                matchesFilter =
                    user.comments_count > 0;

                break;


            case "warnings":

                matchesFilter =
                    user.warnings_count > 0;

                break;


            case "actions":

                matchesFilter =
                    user.actions_count > 0;

                break;


            case "members":

                matchesFilter =
                    user.is_member === true;

                break;


            default:

                matchesFilter = true;

        }


        return matchesSearch && matchesFilter;

    });
}


// ============================================================
// USER LADEN
// ============================================================

async function loadUsers() {

    try {

        const response =
            await fetch("/users/");


        if (!response.ok) {

            throw new Error(
                "Benutzer konnten nicht geladen werden"
            );

        }


        const data =
            await response.json();


        allUsers = data;


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        userList.innerHTML = `

            <div class="alert alert-danger">

                <strong>Fehler:</strong>

                Benutzer konnten nicht geladen werden.

            </div>

        `;

    }
}


// ============================================================
// USER RENDERN
// ============================================================

function renderUsers(users) {

    userList.innerHTML = "";


    if (users.length === 0) {

        userList.innerHTML = `

            <div class="text-center text-muted py-5">

                <div style="font-size: 40px;">
                    🔍
                </div>

                <h5>
                    Keine Benutzer gefunden
                </h5>

                <p>
                    Es wurden keine Benutzer gefunden,
                    die zu deiner Suche passen.
                </p>

            </div>

        `;

        return;
    }


    users.forEach(user => {

        const userCard =
            document.createElement("div");


        userCard.className =
            "card mb-3 user-card";


        // ====================================================
        // KOMMENTARE
        // ====================================================

        const commentsHtml =
            user.comments &&
            user.comments.length

            ? user.comments.map(comment => `

                <div class="user-entry">

                    <div class="user-entry-content">

                        <span class="user-entry-author">
                            ${escapeHtml(comment.author)}
                        </span>

                        <span class="user-entry-text">
                            ${escapeHtml(comment.comment)}
                        </span>

                    </div>


                    <button
                        type="button"
                        class="btn btn-danger btn-sm delete-comment-btn"
                        data-id="${comment.id}"
                    >
                        Löschen
                    </button>

                </div>

            `).join("")

            : `

                <div class="text-muted small py-2">
                    Keine Kommentare vorhanden.
                </div>

            `;


        // ====================================================
        // WARNINGS
        // ====================================================

        const warningsHtml =
            user.warnings &&
            user.warnings.length

            ? user.warnings.map(warning => `

                <div class="user-entry">

                    <div class="user-entry-content">

                        <span class="user-entry-time">
                            ${escapeHtml(warning.time)}
                        </span>

                        <span class="user-entry-text">
                            ${escapeHtml(warning.comment)}
                        </span>

                    </div>


                    <button
                        type="button"
                        class="btn btn-danger btn-sm delete-warning-btn"
                        data-id="${warning.id}"
                    >
                        Löschen
                    </button>

                </div>

            `).join("")

            : `

                <div class="text-muted small py-2">
                    Keine Warnings vorhanden.
                </div>

            `;


        // ====================================================
        // GROUP ACTIONS
        // ====================================================

        const actionsHtml =
            user.group_actions &&
            user.group_actions.length

            ? user.group_actions.map(action => `

                <div class="user-entry">

                    <div class="user-entry-content">

                        <span class="user-entry-time">
                            ${escapeHtml(action.time)}
                        </span>

                        <span class="user-entry-text">
                            ${escapeHtml(action.action)}
                        </span>

                    </div>


                    <button
                        type="button"
                        class="btn btn-danger btn-sm delete-action-btn"
                        data-id="${action.id}"
                    >
                        Löschen
                    </button>

                </div>

            `).join("")

            : `

                <div class="text-muted small py-2">
                    Keine Aktionen vorhanden.
                </div>

            `;


        // ====================================================
        // USER CARD
        // ====================================================

        userCard.innerHTML = `

            <div class="card-body">


                <!-- ======================================== -->
                <!-- HEADER -->
                <!-- ======================================== -->

                <div class="d-flex justify-content-between align-items-center mb-3">

                    <div>

                        <div class="d-flex align-items-center gap-2 flex-wrap">

                            <span class="badge bg-secondary">
                                #${user.id}
                            </span>


                            <h5 class="mb-0">
                                ${escapeHtml(user.username)}
                            </h5>


                            ${
                                user.is_member

                                ? `
                                    <span class="badge bg-success">
                                        Mitglied
                                    </span>
                                `

                                : `
                                    <span class="badge bg-secondary">
                                        Kein Mitglied
                                    </span>
                                `
                            }

                        </div>


                        <div class="text-muted small mt-1">

                            Discord-ID:

                            <span class="user-discord-id">
                                ${escapeHtml(user.user_id)}
                            </span>

                        </div>

                    </div>


                    <div class="d-flex gap-2">

                        <button
                            type="button"
                            class="btn btn-warning btn-sm edit-user-btn"
                        >
                            Bearbeiten
                        </button>


                        <button
                            type="button"
                            class="btn btn-danger btn-sm delete-user-btn"
                        >
                            Löschen
                        </button>

                    </div>

                </div>


                <!-- ======================================== -->
                <!-- BASISDATEN -->
                <!-- ======================================== -->

                <div class="row g-2 mb-3">


                    <div class="col-md-4">

                        <div class="user-info-box">

                            <div class="user-info-label">
                                Beitritt
                            </div>


                            <div class="user-info-value">

                                ${escapeHtml(
                                    user.join_date
                                )}

                            </div>

                        </div>

                    </div>


                    <!-- ==================================== -->
                    <!-- UPRANK -->
                    <!-- ==================================== -->

                    <div class="col-md-4">

                        <div class="user-info-box">

                            <div class="user-info-label">
                                Letzte Beförderung
                            </div>


                            <div class="user-info-value d-flex justify-content-between align-items-center gap-2">

                                <span>

                                    ${
                                        escapeHtml(
                                            user.last_uprank
                                        ) || "Noch nie"

                                    }

                                </span>


                                <button
                                    type="button"
                                    class="btn btn-success btn-sm uprank-user-btn"
                                    title="Jetzt als befördert markieren"
                                >
                                    ⬆️ Uprank
                                </button>

                            </div>

                        </div>

                    </div>


                    <div class="col-md-4">

                        <div class="user-info-box">

                            <div class="user-info-label">
                                Onlinezeit
                            </div>


                            <div class="user-info-value">

                                ${formatOnlineTime(
                                    user.online_time
                                )}

                            </div>

                        </div>

                    </div>

                </div>


                <!-- ======================================== -->
                <!-- MITGLIEDSSTATUS -->
                <!-- ======================================== -->

                <div class="user-section">

                    <div class="d-flex justify-content-between align-items-center">

                        <div>

                            <strong>
                                Mitgliedsstatus
                            </strong>


                            <div class="text-muted small">

                                ${
                                    user.is_member

                                    ? "Dieser Benutzer ist aktives Mitglied."

                                    : "Dieser Benutzer ist kein aktives Mitglied."
                                }

                            </div>

                        </div>


                        <button
                            type="button"
                            class="btn btn-sm ${
                                user.is_member
                                    ? "btn-outline-danger"
                                    : "btn-outline-success"
                            } toggle-member-btn"
                        >

                            ${
                                user.is_member
                                    ? "Mitgliedschaft entfernen"
                                    : "Zum Mitglied machen"
                            }

                        </button>

                    </div>

                </div>


                ${
                    user.is_member

                    ? `

                        <!-- ======================================== -->
                        <!-- MITGLIEDSDATEN -->
                        <!-- ======================================== -->

                        <div class="user-section">

                            <div class="d-flex justify-content-between align-items-center">

                                <div>

                                    <strong>
                                        Gangbeitrag
                                    </strong>


                                    <div class="text-muted small">

                                        ${
                                            user.has_payed

                                            ? "Beitrag wurde bezahlt."

                                            : "Beitrag ist noch offen."
                                        }

                                    </div>

                                </div>


                                <button
                                    type="button"
                                    class="btn btn-sm ${
                                        user.has_payed
                                            ? "btn-outline-danger"
                                            : "btn-outline-success"
                                    } toggle-payment-btn"
                                >

                                    ${
                                        user.has_payed
                                            ? "Als offen markieren"
                                            : "Als bezahlt markieren"
                                    }

                                </button>

                            </div>

                        </div>


                        <!-- ======================================== -->
                        <!-- STATUS -->
                        <!-- ======================================== -->

                        <div class="user-section">

                            <div class="d-flex justify-content-between align-items-center">

                                <div>

                                    <strong>
                                        Status
                                    </strong>


                                    <div class="text-muted small">

                                        ${getStatusText(
                                            user.status
                                        )}

                                    </div>

                                </div>

                            </div>

                        </div>

                    `

                    : ""
                }


                <!-- ======================================== -->
                <!-- STATISTIK -->
                <!-- ======================================== -->

                <div class="user-section">

                    <div class="row g-2">


                        <div class="col-md-4">

                            <div class="user-stat">

                                <div class="user-stat-number">
                                    ${user.comments_count}
                                </div>

                                <div class="user-stat-label">
                                    Kommentare
                                </div>

                            </div>

                        </div>


                        <div class="col-md-4">

                            <div class="user-stat">

                                <div class="user-stat-number">
                                    ${user.warnings_count}
                                </div>

                                <div class="user-stat-label">
                                    Warnings
                                </div>

                            </div>

                        </div>


                        <div class="col-md-4">

                            <div class="user-stat">

                                <div class="user-stat-number">
                                    ${user.actions_count}
                                </div>

                                <div class="user-stat-label">
                                    Aktionen
                                </div>

                            </div>

                        </div>

                    </div>

                </div>


                <!-- ======================================== -->
                <!-- KOMMENTARE -->
                <!-- ======================================== -->

                <div class="user-section">

                    <h6 class="user-section-title">
                        💬 Kommentare
                    </h6>


                    <div id="comments-${user.id}">

                        ${commentsHtml}

                    </div>


                    <div class="input-group mt-2">

                        <input
                            type="text"
                            id="commentInput-${user.id}"
                            class="form-control"
                            placeholder="Neuer Kommentar"
                        >


                        <button
                            type="button"
                            class="btn btn-primary add-comment-btn"
                        >
                            Hinzufügen
                        </button>

                    </div>

                </div>


                <!-- ======================================== -->
                <!-- WARNINGS -->
                <!-- ======================================== -->

                <div class="user-section">

                    <h6 class="user-section-title">
                        ⚠️ Warnings
                    </h6>


                    <div id="warnings-${user.id}">

                        ${warningsHtml}

                    </div>


                    <div class="input-group mt-2">

                        <input
                            type="text"
                            id="warningInput-${user.id}"
                            class="form-control"
                            placeholder="Neue Warning"
                        >


                        <button
                            type="button"
                            class="btn btn-primary add-warning-btn"
                        >
                            Hinzufügen
                        </button>

                    </div>

                </div>


                <!-- ======================================== -->
                <!-- GROUP ACTIONS -->
                <!-- ======================================== -->

                <div class="user-section">

                    <h6 class="user-section-title">
                        📋 Group Actions
                    </h6>


                    <div id="actions-${user.id}">

                        ${actionsHtml}

                    </div>


                    <div class="input-group mt-2">

                        <input
                            type="text"
                            id="actionInput-${user.id}"
                            class="form-control"
                            placeholder="Neue Aktion"
                        >


                        <button
                            type="button"
                            class="btn btn-primary add-action-btn"
                        >
                            Hinzufügen
                        </button>

                    </div>

                </div>

            </div>

        `;


        userList.appendChild(userCard);


        // ====================================================
        // EVENTS
        // ====================================================

        userCard
            .querySelector(".edit-user-btn")
            .addEventListener("click", () => {

                openEditModal(user);

            });


        userCard
            .querySelector(".delete-user-btn")
            .addEventListener("click", () => {

                deleteUser(user.id);

            });


        // ====================================================
        // UPRANK BUTTON
        // ====================================================

        userCard
            .querySelector(".uprank-user-btn")
            .addEventListener("click", () => {

                uprankUser(user.id);

            });


        // ====================================================
        // MITGLIEDSSTATUS
        // ====================================================

        userCard
            .querySelector(".toggle-member-btn")
            .addEventListener("click", () => {

                toggleMemberStatus(user.id);

            });


        // ====================================================
        // BEITRAGSSTATUS
        // ====================================================

        if (user.is_member) {

            userCard
                .querySelector(".toggle-payment-btn")
                .addEventListener("click", () => {

                    togglePaymentStatus(user.id);

                });

        }


        // ====================================================
        // KOMMENTAR
        // ====================================================

        userCard
            .querySelector(".add-comment-btn")
            .addEventListener("click", () => {

                addComment(user.id);

            });


        // ====================================================
        // WARNING
        // ====================================================

        userCard
            .querySelector(".add-warning-btn")
            .addEventListener("click", () => {

                addWarning(user.id);

            });


        // ====================================================
        // GROUP ACTION
        // ====================================================

        userCard
            .querySelector(".add-action-btn")
            .addEventListener("click", () => {

                addAction(user.id);

            });


        // ====================================================
        // KOMMENTARE LÖSCHEN
        // ====================================================

        userCard
            .querySelectorAll(".delete-comment-btn")
            .forEach(button => {

                button.addEventListener("click", () => {

                    deleteComment(
                        button.dataset.id
                    );

                });

            });


        // ====================================================
        // WARNINGS LÖSCHEN
        // ====================================================

        userCard
            .querySelectorAll(".delete-warning-btn")
            .forEach(button => {

                button.addEventListener("click", () => {

                    deleteWarning(
                        button.dataset.id
                    );

                });

            });


        // ====================================================
        // ACTIONS LÖSCHEN
        // ====================================================

        userCard
            .querySelectorAll(".delete-action-btn")
            .forEach(button => {

                button.addEventListener("click", () => {

                    deleteAction(
                        button.dataset.id
                    );

                });

            });

    });
}


// ============================================================
// SUCHE / FILTER
// ============================================================

function applySearchFilter() {

    renderUsers(
        getFilteredUsers()
    );

}


document
    .getElementById("searchInput")
    .addEventListener(
        "input",
        applySearchFilter
    );


document
    .getElementById("filterSelect")
    .addEventListener(
        "change",
        applySearchFilter
    );


// ============================================================
// EDIT MODAL
// ============================================================

function openEditModal(user) {

    currentEditUserId =
        user.id;


    document
        .getElementById("editUsername")
        .value =
            user.username || "";


    document
        .getElementById("editJoinDate")
        .value =
            user.join_date || "";


    document
        .getElementById("statusSelect")
        .value =
            user.status || "active";


    const modalElement =
        document.getElementById(
            "editUserModal"
        );


    const modal =
        bootstrap.Modal
            .getOrCreateInstance(
                modalElement
            );


    modal.show();

}


// ============================================================
// USER BEARBEITEN
// ============================================================

document
    .getElementById("saveEditBtn")
    .addEventListener(
        "click",
        async () => {

            if (!currentEditUserId) {
                return;
            }


            const payload = {

                username:
                    document
                        .getElementById(
                            "editUsername"
                        )
                        .value
                        .trim(),

                join_date:
                    document
                        .getElementById(
                            "editJoinDate"
                        )
                        .value
                        .trim(),

                status:
                    document
                        .getElementById(
                            "statusSelect"
                        )
                        .value

            };


            if (!payload.username) {

                alert(
                    "Bitte einen Benutzernamen eingeben."
                );

                return;

            }


            try {

                const response =
                    await fetch(
                        `/users/${currentEditUserId}`,
                        {
                            method: "PUT",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(
                                    payload
                                )
                        }
                    );


                if (!response.ok) {

                    throw new Error(
                        "Benutzer konnte nicht aktualisiert werden"
                    );

                }


                const user =
                    allUsers.find(
                        u =>
                            u.id ===
                            currentEditUserId
                    );


                if (user) {

                    user.username =
                        payload.username;

                    user.join_date =
                        payload.join_date;

                    user.status =
                        payload.status;

                }


                bootstrap
                    .Modal
                    .getInstance(
                        document.getElementById(
                            "editUserModal"
                        )
                    )
                    .hide();


                renderUsers(
                    getFilteredUsers()
                );


            } catch (error) {

                console.error(error);


                alert(
                    "Benutzer konnte nicht aktualisiert werden."
                );

            }

        }
    );


// ============================================================
// USER LÖSCHEN
// ============================================================

async function deleteUser(userId) {

    const user =
        allUsers.find(
            u => u.id === userId
        );


    if (!user) {
        return;
    }


    if (
        !confirm(
            `Soll der Benutzer "${user.username}" wirklich gelöscht werden?`
        )
    ) {
        return;
    }


    try {

        const response =
            await fetch(
                `/users/${userId}`,
                {
                    method: "DELETE"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Benutzer konnte nicht gelöscht werden"
            );

        }


        allUsers =
            allUsers.filter(
                u => u.id !== userId
            );


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "Benutzer konnte nicht gelöscht werden."
        );

    }

}


// ============================================================
// UPRANK
// ============================================================

async function uprankUser(userId) {

    const user =
        allUsers.find(
            u => u.id === userId
        );


    if (!user) {
        return;
    }


    if (
        !confirm(
            `Möchtest du "${user.username}" wirklich upranken?`
        )
    ) {
        return;
    }


    const now =
        new Date();


    const day =
        String(
            now.getDate()
        ).padStart(2, "0");


    const month =
        String(
            now.getMonth() + 1
        ).padStart(2, "0");


    const year =
        now.getFullYear();


    const hours =
        String(
            now.getHours()
        ).padStart(2, "0");


    const minutes =
        String(
            now.getMinutes()
        ).padStart(2, "0");


    const formattedDate =
        `${day}.${month}.${year} ${hours}:${minutes}`;


    try {

        const response =
            await fetch(
                `/users/${userId}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            last_uprank:
                                formattedDate
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "Uprank fehlgeschlagen"
            );

        }


        user.last_uprank =
            formattedDate;


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "Uprank konnte nicht gespeichert werden."
        );

    }

}


// ============================================================
// MITGLIEDSSTATUS
// ============================================================

async function toggleMemberStatus(userId) {

    const user =
        allUsers.find(
            u => u.id === userId
        );


    if (!user) {
        return;
    }


    const newStatus =
        !user.is_member;


    try {

        const response =
            await fetch(
                `/users/${userId}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            is_member:
                                newStatus
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "Mitgliedsstatus konnte nicht geändert werden"
            );

        }


        user.is_member =
            newStatus;


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "Mitgliedsstatus konnte nicht geändert werden."
        );

    }

}


// ============================================================
// BEITRAGSSTATUS
// ============================================================

async function togglePaymentStatus(userId) {

    const user =
        allUsers.find(
            u => u.id === userId
        );


    if (!user) {
        return;
    }


    const newStatus =
        !user.has_payed;


    try {

        const response =
            await fetch(
                `/users/${userId}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            has_payed:
                                newStatus
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "Beitragsstatus konnte nicht geändert werden"
            );

        }


        user.has_payed =
            newStatus;


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "Gangbeitrag konnte nicht geändert werden."
        );

    }

}


// ============================================================
// ALLE BEITRÄGE ZURÜCKSETZEN
// ============================================================

async function resetAllPayments() {

    if (
        !confirm(
            "Möchtest du wirklich bei allen Nutzern den Gangbeitrag zurücksetzen?"
        )
    ) {
        return;
    }


    try {

        const response =
            await fetch(
                "/users/reset-payments",
                {
                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    }
                }
            );


        if (!response.ok) {

            throw new Error(
                "Beiträge konnten nicht zurückgesetzt werden"
            );

        }


        allUsers.forEach(user => {

            user.has_payed =
                false;

        });


        renderUsers(
            getFilteredUsers()
        );


        alert(
            "Alle Gangbeiträge wurden zurückgesetzt."
        );


    } catch (error) {

        console.error(error);


        alert(
            "Fehler beim Zurücksetzen der Beiträge."
        );

    }

}


// ============================================================
// OFFENE BEITRÄGE
// ============================================================

function showUnpaidMembers() {

    const list =
        document.getElementById(
            "unpaidMembersList"
        );


    list.innerHTML = "";


    const unpaidMembers =
        allUsers.filter(
            user =>
                user.is_member &&
                !user.has_payed
        );


    if (
        unpaidMembers.length === 0
    ) {

        list.innerHTML = `

            <li class="list-group-item">

                🟢 Alle Mitglieder haben bezahlt

            </li>

        `;

    } else {

        unpaidMembers.forEach(user => {

            const li =
                document.createElement(
                    "li"
                );


            li.className =
                "list-group-item d-flex justify-content-between align-items-center";


            li.innerHTML = `

                <span>
                    ${escapeHtml(user.username)}
                </span>


                <span class="badge bg-danger">
                    Offen
                </span>

            `;


            list.appendChild(li);

        });

    }


    const modal =
        bootstrap.Modal.getOrCreateInstance(
            document.getElementById(
                "unpaidMembersModal"
            )
        );


    modal.show();

}


// ============================================================
// KOMMENTAR HINZUFÜGEN
// ============================================================

async function addComment(userId) {

    const input =
        document.getElementById(
            `commentInput-${userId}`
        );


    const comment =
        input.value.trim();


    if (!comment) {
        return;
    }


    try {

        const response =
            await fetch(
                `/users/${userId}/comments`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            author: "Admin",
                            comment: comment
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "Kommentar konnte nicht hinzugefügt werden"
            );

        }


        const result =
            await response.json();


        const user =
            allUsers.find(
                u => u.id === userId
            );


        if (user) {

            user.comments.push({

                id: result.id,

                author: "Admin",

                comment: comment

            });


            user.comments_count =
                user.comments.length;

        }


        input.value = "";


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "Kommentar konnte nicht hinzugefügt werden."
        );

    }

}


// ============================================================
// WARNING HINZUFÜGEN
// ============================================================

async function addWarning(userId) {

    const input =
        document.getElementById(
            `warningInput-${userId}`
        );


    const comment =
        input.value.trim();


    if (!comment) {
        return;
    }


    try {

        const response =
            await fetch(
                `/users/${userId}/warnings`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            comment: comment
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "Warning konnte nicht hinzugefügt werden"
            );

        }


        const result =
            await response.json();


        const user =
            allUsers.find(
                u => u.id === userId
            );


        if (user) {

            user.warnings.push({

                id: result.id,

                time:
                    new Date()
                        .toLocaleString("de-DE"),

                comment: comment

            });


            user.warnings_count =
                user.warnings.length;

        }


        input.value = "";


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "Warning konnte nicht hinzugefügt werden."
        );

    }

}


// ============================================================
// GROUP ACTION HINZUFÜGEN
// ============================================================

async function addAction(userId) {

    const input =
        document.getElementById(
            `actionInput-${userId}`
        );


    const action =
        input.value.trim();


    if (!action) {
        return;
    }


    try {

        const response =
            await fetch(
                `/users/${userId}/group_actions`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            action: action
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "Aktion konnte nicht hinzugefügt werden"
            );

        }


        const result =
            await response.json();


        const user =
            allUsers.find(
                u => u.id === userId
            );


        if (user) {

            user.group_actions.push({

                id: result.id,

                time:
                    new Date()
                        .toLocaleString("de-DE"),

                action: action

            });


            user.actions_count =
                user.group_actions.length;

        }


        input.value = "";


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "Aktion konnte nicht hinzugefügt werden."
        );

    }

}


// ============================================================
// KOMMENTAR LÖSCHEN
// ============================================================

async function deleteComment(commentId) {

    if (
        !confirm(
            "Kommentar wirklich löschen?"
        )
    ) {
        return;
    }


    try {

        const response =
            await fetch(
                `/users/comments/${commentId}`,
                {
                    method: "DELETE"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Kommentar konnte nicht gelöscht werden"
            );

        }


        allUsers.forEach(user => {

            user.comments =
                user.comments.filter(
                    comment =>
                        comment.id !==
                        Number(commentId)
                );


            user.comments_count =
                user.comments.length;

        });


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "Kommentar konnte nicht gelöscht werden."
        );

    }

}


// ============================================================
// WARNING LÖSCHEN
// ============================================================

async function deleteWarning(warningId) {

    if (
        !confirm(
            "Warning wirklich löschen?"
        )
    ) {
        return;
    }


    try {

        const response =
            await fetch(
                `/users/warnings/${warningId}`,
                {
                    method: "DELETE"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Warning konnte nicht gelöscht werden"
            );

        }


        allUsers.forEach(user => {

            user.warnings =
                user.warnings.filter(
                    warning =>
                        warning.id !==
                        Number(warningId)
                );


            user.warnings_count =
                user.warnings.length;

        });


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "Warning konnte nicht gelöscht werden."
        );

    }

}


// ============================================================
// GROUP ACTION LÖSCHEN
// ============================================================

async function deleteAction(actionId) {

    if (
        !confirm(
            "GroupAction wirklich löschen?"
        )
    ) {
        return;
    }


    try {

        const response =
            await fetch(
                `/users/group_actions/${actionId}`,
                {
                    method: "DELETE"
                }
            );


        if (!response.ok) {

            throw new Error(
                "GroupAction konnte nicht gelöscht werden"
            );

        }


        allUsers.forEach(user => {

            user.group_actions =
                user.group_actions.filter(
                    action =>
                        action.id !==
                        Number(actionId)
                );


            user.actions_count =
                user.group_actions.length;

        });


        renderUsers(
            getFilteredUsers()
        );


    } catch (error) {

        console.error(error);


        alert(
            "GroupAction konnte nicht gelöscht werden."
        );

    }

}


// ============================================================
// ENTER = EINGABE ABSENDEN
// ============================================================

document.addEventListener(
    "keydown",
    event => {

        if (event.key !== "Enter") {
            return;
        }


        const target =
            event.target;


        // ----------------------------------------------------
        // KOMMENTAR
        // ----------------------------------------------------

        if (
            target.id &&
            target.id.startsWith(
                "commentInput-"
            )
        ) {

            const userId =
                Number(
                    target.id.replace(
                        "commentInput-",
                        ""
                    )
                );


            addComment(userId);

        }


        // ----------------------------------------------------
        // WARNING
        // ----------------------------------------------------

        if (
            target.id &&
            target.id.startsWith(
                "warningInput-"
            )
        ) {

            const userId =
                Number(
                    target.id.replace(
                        "warningInput-",
                        ""
                    )
                );


            addWarning(userId);

        }


        // ----------------------------------------------------
        // GROUP ACTION
        // ----------------------------------------------------

        if (
            target.id &&
            target.id.startsWith(
                "actionInput-"
            )
        ) {

            const userId =
                Number(
                    target.id.replace(
                        "actionInput-",
                        ""
                    )
                );


            addAction(userId);

        }

    }
);


// ============================================================
// START
// ============================================================

loadUsers();