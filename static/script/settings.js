let rawSettings = {};

async function loadSettings() {
    const res = await fetch("/settings/api");

    const grouped = await res.json();
    const tabs = document.getElementById("settingsTabs");
    const contents = document.getElementById("settingsTabContent");
    tabs.innerHTML = "";
    contents.innerHTML = "";
    let first = true;

    for (const group in grouped) {
        const safeGroup = group.replace(/\s+/g, "_");
        tabs.innerHTML += `
            <li class="nav-item" role="presentation">
                <button
                    class="nav-link ${first ? 'active' : ''}"
                    id="tab-${safeGroup}"
                    data-bs-toggle="tab"
                    data-bs-target="#content-${safeGroup}"
                    type="button"
                    role="tab"
                >
                ${group}
                </button>
            </li>
        `;
        let inputs = "";
        for (const key in grouped[group]) {
            const fullKey = `${group}.${key}`;
            const value = grouped[group][key];
            inputs += `
                <div class="mb-3">
                    <label class="form-label">${key}</label>
                     <input
                        type="text"
                        class="form-control"
                        id="setting-${fullKey}"
                        value="${value}"
                     >
                </div>
            `;
            rawSettings[fullKey] = value;
         }

            contents.innerHTML += `
                <div
                    class="tab-pane fade ${first ? 'show active' : ''}"
                    id="content-${safeGroup}"
                    role="tabpanel"
                >
                    ${inputs}
                </div>
            `;

            first = false;
        }
    }
async function saveSettings() {
    const inputs = document.querySelectorAll("#settingsTabContent input");
    const newData = {};

    inputs.forEach(input => {
        const key = input.id.replace("setting-", "");
        newData[key] = input.value;
    });

    await fetch("/settings/api", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(newData)
     });
     alert("Einstellungen gespeichert!");
}
loadSettings();
