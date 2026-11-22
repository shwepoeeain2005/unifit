(() => {
    const list = document.querySelector(".card-group");
    const template = document.getElementById("university-card-template");
    const search = document.getElementById("search");
    const buttons = [...document.querySelectorAll(".filter-buttons button[data-category]")];
    const noResults = document.getElementById("no-results-message");
    const campusAliases = {
        ytu: "universities/YTU.html", wytu: "universities/WYTU.html", ttu: "universities/TTU.html",
        mtu: "universities/MTU.html", tum: "universities/TUM.html", ucsy: "universities/UCSY.html",
        ucsm: "universities/UCSM.html", uit: "universities/UIT.html", miit: "universities/MIIT.html",
        nspu: "universities/NSPU.html", ns: "universities/NSPU.html",
    };
    const categoryAliases = { t: "tu", tu: "tu", cu: "cu" };
    const cards = [];
    let selectedCategory = "all";

    for (const record of window.unifitCards) {
        const card = template.content.firstElementChild.cloneNode(true);
        card.className = `card ${record.categories}`;
        card.querySelector("h1").textContent = record.name;
        card.querySelector("p").textContent = record.address;
        if (!record.has_line_break) card.querySelector("br").remove();
        const image = card.querySelector("img");
        if (record.image_path) image.setAttribute("src", record.image_path);
        const button = card.querySelector("button");
        if (record.detail_url) {
            card.dataset.detailUrl = record.detail_url;
            button.addEventListener("click", () => { window.location.href = record.detail_url; });
        }
        list.appendChild(card);
        cards.push({ card, text: card.textContent.toLowerCase(), name: record.name });
    }

    function applyFilters() {
        const query = search.value.trim().toLowerCase();
        const campus = Object.hasOwn(campusAliases, query) ? campusAliases[query] : null;
        const category = Object.hasOwn(categoryAliases, query) ? categoryAliases[query] : null;
        const polytechnicSearch = query === "pu" || query === "poly";

        let visibleCount = 0;
        for (const { card, text, name } of cards) {
            const matchesCategory = selectedCategory === "all" || card.classList.contains(selectedCategory);
            const matchesSearch = campus ? card.dataset.detailUrl === campus
                : category ? card.classList.contains(category)
                : polytechnicSearch ? /polytec(?:hnic|hinc)/i.test(name) : text.includes(query);
            const visible = matchesCategory && matchesSearch;
            card.style.display = visible ? "block" : "none";
            if (visible) visibleCount++;
        }
        noResults.style.display = visibleCount ? "none" : "flex";
    }

    for (const button of buttons) {
        button.addEventListener("click", () => {
            selectedCategory = button.dataset.category;
            for (const option of buttons) {
                const active = option === button;
                option.classList.toggle("active", active);
                option.setAttribute("aria-pressed", String(active));
            }
            applyFilters();
        });
    }
    search.addEventListener("input", applyFilters);
    applyFilters();
})();
