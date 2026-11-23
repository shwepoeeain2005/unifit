(() => {
    const list = document.querySelector(".card-group");
    const template = document.getElementById("university-card-template");
    const search = document.getElementById("search");
    const searchClear = document.getElementById("search-clear");
    const clearFilters = document.getElementById("clear-filters");
    const emptyClear = document.getElementById("empty-clear");
    const filterTrack = document.getElementById("filter-buttons");
    const filterPrev = document.getElementById("filter-prev");
    const filterNext = document.getElementById("filter-next");
    const buttons = [...document.querySelectorAll(".filter-buttons button[data-category]")];
    const noResults = document.getElementById("no-results-message");
    const resultsCount = document.getElementById("results-count");
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (!list || !template || !search || !window.unifitCards) {
        throw new Error("UniFit university list page is missing required markup or data.");
    }

    const campusAliases = {
        ytu: "universities/ytu.html",
        wytu: "universities/wytu.html",
        ttu: "universities/ttu.html",
        mtu: "universities/mtu.html",
        tum: "universities/tum.html",
        ucsy: "universities/ucsy.html",
        ucsm: "universities/ucsm.html",
        uit: "universities/uit.html",
        miit: "universities/miit.html",
        nspu: "universities/nspu.html",
        ns: "universities/nspu.html",
    };
    const categoryAliases = { t: "tu", tu: "tu", cu: "cu" };

    const cards = [];
    let selectedCategory = "all";
    const totalCount = window.unifitCards.length;

    function cleanAddress(address) {
        return String(address || "")
            .replace(/^📍\s*/u, "")
            .replace(/📍/gu, "")
            .replace(/\s+/g, " ")
            .trim();
    }

    function categoryLabel(raw) {
        if (typeof window.unifitCategoryLabel === "function") {
            return window.unifitCategoryLabel(raw);
        }
        return String(raw || "").trim() || "University";
    }

    function setupAddressToggle(card) {
        const address = card.querySelector(".card-address");
        const moreBtn = card.querySelector(".card-address-more");
        if (!address || !moreBtn) return;

        const syncOverflow = () => {
            if (address.classList.contains("is-expanded")) return;
            moreBtn.hidden = address.scrollHeight <= address.clientHeight + 1;
        };

        moreBtn.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            const expanded = address.classList.toggle("is-expanded");
            moreBtn.textContent = expanded ? "Show less" : "Show more";
            moreBtn.setAttribute("aria-expanded", String(expanded));
            if (!expanded) syncOverflow();
        });

        moreBtn.setAttribute("aria-expanded", "false");
        requestAnimationFrame(syncOverflow);
        window.addEventListener("resize", syncOverflow, { passive: true });
    }

    for (const record of window.unifitCards) {
        const card = template.content.firstElementChild.cloneNode(true);
        card.className = `card uni-card ${record.categories}`.trim();

        const title = card.querySelector(".card-title");
        const address = card.querySelector(".card-address");
        const category = card.querySelector(".card-category");
        const image = card.querySelector("img");
        const cta = card.querySelector(".card-cta");

        title.textContent = record.name;
        address.textContent = cleanAddress(record.address) || "Myanmar";
        category.textContent = categoryLabel(record.categories);

        if (record.image_path) {
            image.setAttribute("src", record.image_path);
            image.setAttribute("alt", record.name);
            image.setAttribute("loading", "lazy");
            image.setAttribute("decoding", "async");
        }

        if (record.detail_url && cta) {
            card.dataset.detailUrl = record.detail_url;
            cta.href = record.detail_url;
            cta.setAttribute("aria-label", `Explore details for ${record.name}`);
            card.classList.add("is-clickable");
            card.addEventListener("click", (event) => {
                if (event.target.closest(".card-address-more, .card-cta, a, button")) return;
                window.location.href = record.detail_url;
            });
            card.addEventListener("keydown", (event) => {
                if (event.target !== card) return;
                if (event.key !== "Enter" && event.key !== " ") return;
                event.preventDefault();
                window.location.href = record.detail_url;
            });
            card.tabIndex = 0;
            card.setAttribute("role", "link");
            card.setAttribute("aria-label", `${record.name}. Explore details`);
        }

        list.appendChild(card);
        setupAddressToggle(card);
        cards.push({
            card,
            text: `${record.name} ${cleanAddress(record.address)}`.toLowerCase(),
            name: record.name,
        });
    }

    function filtersActive() {
        return selectedCategory !== "all" || search.value.trim().length > 0;
    }

    function syncClearControls() {
        const active = filtersActive();
        if (searchClear) searchClear.hidden = search.value.trim().length === 0;
        if (clearFilters) clearFilters.hidden = !active;
    }

    function updateResults(visibleCount) {
        if (resultsCount) {
            if (visibleCount === totalCount && selectedCategory === "all" && !search.value.trim()) {
                resultsCount.textContent = `${totalCount} universities available`;
            } else if (visibleCount === 1) {
                resultsCount.textContent = `Showing 1 of ${totalCount} Universities`;
            } else {
                resultsCount.textContent = `Showing ${visibleCount} of ${totalCount} Universities`;
            }
        }

        if (!noResults) return;
        const empty = visibleCount === 0;
        noResults.hidden = !empty;
        noResults.classList.toggle("is-visible", empty);
        noResults.style.display = empty ? "flex" : "none";
        syncClearControls();
    }

    function applyFilters() {
        const query = search.value.trim().toLowerCase();
        const campus = Object.hasOwn(campusAliases, query) ? campusAliases[query] : null;
        const category = Object.hasOwn(categoryAliases, query) ? categoryAliases[query] : null;
        const polytechnicSearch = query === "pu" || query === "poly";

        let visibleCount = 0;
        let stagger = 0;
        for (const { card, text, name } of cards) {
            const matchesCategory =
                selectedCategory === "all" || card.classList.contains(selectedCategory);
            const matchesSearch = campus
                ? card.dataset.detailUrl === campus
                : category
                  ? card.classList.contains(category)
                  : polytechnicSearch
                    ? /polytec(?:hnic|hinc)/i.test(name)
                    : text.includes(query);
            const visible = matchesCategory && matchesSearch;
            card.style.display = visible ? "" : "none";
            if (visible) {
                visibleCount += 1;
                if (!prefersReducedMotion) {
                    card.classList.remove("is-visible");
                    void card.offsetWidth;
                    card.style.animationDelay = `${Math.min(stagger, 10) * 40}ms`;
                    card.classList.add("is-visible");
                    stagger += 1;
                }
            }
        }
        updateResults(visibleCount);
    }

    function setCategory(category) {
        selectedCategory = category;
        for (const option of buttons) {
            const active = option.dataset.category === category;
            option.classList.toggle("active", active);
            option.setAttribute("aria-pressed", String(active));
        }
        applyFilters();
    }

    function resetFilters() {
        search.value = "";
        setCategory("all");
        search.focus();
    }

    for (const button of buttons) {
        button.addEventListener("click", () => {
            setCategory(button.dataset.category);
        });
    }

    search.addEventListener("input", applyFilters);

    if (searchClear) {
        searchClear.addEventListener("click", () => {
            search.value = "";
            applyFilters();
            search.focus();
        });
    }

    if (clearFilters) clearFilters.addEventListener("click", resetFilters);
    if (emptyClear) emptyClear.addEventListener("click", resetFilters);

    function updateFilterScrollControls() {
        if (!filterTrack || !filterPrev || !filterNext) return;
        const maxScroll = filterTrack.scrollWidth - filterTrack.clientWidth;
        const needsScroll = maxScroll > 8;
        filterPrev.hidden = !needsScroll;
        filterNext.hidden = !needsScroll;
        if (!needsScroll) return;
        filterPrev.disabled = filterTrack.scrollLeft <= 4;
        filterNext.disabled = filterTrack.scrollLeft >= maxScroll - 4;
        filterPrev.style.opacity = filterPrev.disabled ? "0.35" : "1";
        filterNext.style.opacity = filterNext.disabled ? "0.35" : "1";
    }

    if (filterTrack && filterPrev && filterNext) {
        filterPrev.addEventListener("click", () => {
            filterTrack.scrollBy({ left: -220, behavior: prefersReducedMotion ? "auto" : "smooth" });
        });
        filterNext.addEventListener("click", () => {
            filterTrack.scrollBy({ left: 220, behavior: prefersReducedMotion ? "auto" : "smooth" });
        });
        filterTrack.addEventListener("scroll", updateFilterScrollControls, { passive: true });
        window.addEventListener("resize", updateFilterScrollControls);
        updateFilterScrollControls();
    }

    const requestedCategory = new URLSearchParams(window.location.search).get("category");
    if (requestedCategory) {
        const match = buttons.find((button) => button.dataset.category === requestedCategory);
        if (match) setCategory(match.dataset.category);
        else applyFilters();
    } else {
        applyFilters();
    }
})();
