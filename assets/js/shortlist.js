(() => {
    const storageKey = "unifit.savedUniversities";
    const campusIds = new Set(window.unifitCards.map((campus) => campus.id));

    function readSaved() {
        try {
            const ids = JSON.parse(localStorage.getItem(storageKey) || "[]");
            return new Set(Array.isArray(ids) ? ids.filter((id) => campusIds.has(id)) : []);
        } catch {
            return new Set();
        }
    }

    let saved = readSaved();

    function refresh() {
        for (const button of document.querySelectorAll("[data-bookmark-id]")) {
            updateButton(button);
        }
        for (const count of document.querySelectorAll("[data-shortlist-count]")) {
            count.textContent = saved.size;
        }
        window.dispatchEvent(new Event("unifit:shortlist-change"));
    }

    function updateButton(button) {
        const pressed = saved.has(Number(button.dataset.bookmarkId));
        button.setAttribute("aria-pressed", String(pressed));
        button.title = pressed ? "Remove from saved universities" : "Save university";
        button.firstElementChild.className = pressed ? "fas fa-bookmark" : "far fa-bookmark";
    }

    function createButton(campus) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "campus-bookmark";
        button.dataset.bookmarkId = campus.id;
        button.setAttribute("aria-label", `Bookmark ${campus.name}`);
        const icon = document.createElement("i");
        icon.setAttribute("aria-hidden", "true");
        button.appendChild(icon);
        updateButton(button);
        button.addEventListener("click", () => {
            const wasSaved = saved.delete(campus.id);
            if (!wasSaved) saved.add(campus.id);
            try {
                localStorage.setItem(storageKey, JSON.stringify([...saved]));
            } catch {
                // The current page can still use the shortlist when storage is unavailable.
            }
            refresh();
        });
        return button;
    }

    window.addEventListener("storage", (event) => {
        if (event.key !== storageKey && event.key !== null) return;
        saved = readSaved();
        refresh();
    });
    window.addEventListener("pageshow", (event) => {
        if (!event.persisted) return;
        saved = readSaved();
        refresh();
    });

    window.unifitShortlist = { has: (id) => saved.has(id), createButton };
    refresh();
})();
