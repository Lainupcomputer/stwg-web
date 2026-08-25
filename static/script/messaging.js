let presets = [];
let editPresetId = null;

async function loadPresets() {
    const res = await fetch("/messaging/api/presets");
    presets = await res.json();
    fillPresetDropdowns();
    fillPresetTable();
}

async function load_history() {
    const msg_res = await fetch("/messaging/api/messages");
    msg_history = await msg_res.json();
    fill_msg_history();
}

function fill_msg_history () {
    const tbody = document.querySelector("#msgTable tbody");
    tbody.innerHTML = "";
     msg_history.forEach(p => {
        tbody.innerHTML += `
            <tr>
                <td>${p.id}</td>
                <td>${p.user_name}</td>
                <td>${p.text}</td>
                <td>${p.date}</td>
            </tr>`;
    });
}

function fillPresetDropdowns() {
    const ann = document.getElementById("annPresetSelect");
    const usr = document.getElementById("msgPresetSelect");

    ann.innerHTML = `<option value="">– Keine Vorlage –</option>`;
    usr.innerHTML = `<option value="">– Keine Vorlage –</option>`;

    presets.forEach(p => {
        const opt = `<option value="${p.text}">${p.title}</option>`;
        if (p.type === "announcement") ann.innerHTML += opt;
        if (p.type === "user") usr.innerHTML += opt;
    });
}

function updateTextFromPreset(type) {
    if (type === 'ann') {
        document.getElementById("annText").value =
            document.getElementById("annPresetSelect").value;
    } else {
        document.getElementById("msgText").value =
            document.getElementById("msgPresetSelect").value;
    }
}

function fillPresetTable() {
    const tbody = document.querySelector("#presetTable tbody");
    tbody.innerHTML = "";

    presets.forEach(p => {
        tbody.innerHTML += `
            <tr>
                <td>${p.type}</td>
                <td>${p.title}</td>
                <td>${p.text}</td>
                <td>
                    <button class="btn btn-warning btn-sm" onclick="editPreset(${p.id})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deletePreset(${p.id})">Delete</button>
                </td>
            </tr>`;
    });
}

function showAddPreset() {
    editPresetId = null;
    document.getElementById("presetModalTitle").innerText = "Neues Preset";
    document.getElementById("modalType").value = "announcement";
    document.getElementById("modalTitle").value = "";
    document.getElementById("modalText").value = "";
    new bootstrap.Modal(document.getElementById("presetModal")).show();
}

function editPreset(id) {
    editPresetId = id;
    const p = presets.find(x => x.id === id);

    document.getElementById("presetModalTitle").innerText = "Preset bearbeiten";
    document.getElementById("modalType").value = p.type;
    document.getElementById("modalTitle").value = p.title;
    document.getElementById("modalText").value = p.text;

    new bootstrap.Modal(document.getElementById("presetModal")).show();
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("modalSaveBtn").onclick = async () => {
        const data = {
            type: modalType.value,
            title: modalTitle.value,
            text: modalText.value
        };

        const url = editPresetId === null
            ? "/messaging/api/presets"
            : `/messaging/api/presets/${editPresetId}`;

        const method = editPresetId === null ? "POST" : "PUT";

        await fetch(url, {
            method,
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });

        bootstrap.Modal.getInstance(presetModal).hide();
        loadPresets();
    };

    loadPresets();
    load_history();
});

async function deletePreset(id) {
    await fetch(`/messaging/api/presets/${id}`, { method: "DELETE" });
    loadPresets();
}

function sendAnnouncement() {
    fetch("/messaging/api/send/announcement", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ text: annText.value })
    }).then(() => alert("Announcement gesendet!"));
}

async function sendUserMessage() {

    const userId =
        document.getElementById("userSelect").value;

    const text =
        document.getElementById("msgText").value;

    const appendSender =
        document.getElementById("appendSender").checked;

    const appendLeadership =
        document.getElementById("appendLeadership").checked;


    if (!userId) {

        alert("Bitte einen Nutzer auswählen.");

        return;
    }


    if (!text.trim()) {

        alert("Bitte eine Nachricht eingeben.");

        return;
    }


    try {

        const res = await fetch(
            "/messaging/api/send/user",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    userId: userId,

                    text: text,

                    append_sender:
                        appendSender,

                    append_leadership:
                        appendLeadership

                })
            }
        );


        const result =
            await res.json();


        if (!res.ok) {

            throw new Error(
                result.error ||
                "Fehler beim Senden der Nachricht."
            );

        }


        alert("Nachricht gesendet!");


        /*
         * Checkboxen nach erfolgreichem
         * Versand wieder zurücksetzen.
         */

        document.getElementById(
            "appendSender"
        ).checked = false;


        document.getElementById(
            "appendLeadership"
        ).checked = false;


        /*
         * Optional: Textfeld leeren
         */

        document.getElementById(
            "msgText"
        ).value = "";


    } catch (err) {

        alert(
            err.message ||
            "Fehler beim Senden der Nachricht."
        );

    }

}