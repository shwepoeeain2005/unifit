(() => {
    const subjectSets = {
        STEAMS1: [
            { code: "myan", label: "Myanmar" },
            { code: "eng", label: "English" },
            { code: "math", label: "Mathematics" },
            { code: "phy", label: "Physics" },
            { code: "chem", label: "Chemistry" },
            { code: "bio", label: "Biology" },
        ],
        STEAMS2: [
            { code: "myan", label: "Myanmar" },
            { code: "eng", label: "English" },
            { code: "math", label: "Mathematics" },
            { code: "phy", label: "Physics" },
            { code: "chem", label: "Chemistry" },
            { code: "eco", label: "Economics" },
        ],
        STAMS1: [
            { code: "myan", label: "Myanmar" },
            { code: "eng", label: "English" },
            { code: "math", label: "Mathematics" },
            { code: "hist", label: "History" },
            { code: "geo", label: "Geography" },
            { code: "eco", label: "Economics" },
        ],
        STAMS2: [
            { code: "myan", label: "Myanmar" },
            { code: "eng", label: "English" },
            { code: "math", label: "Mathematics" },
            { code: "eco", label: "Economics" },
            { code: "customMyan", label: "စိတ်ကြိုက်မြန်မာစာ" },
            { code: "social", label: "လူမှုရေးသိပ္ပံ" },
        ],
    };

    const REGION_PATTERNS = [
        { id: "yangon", label: "Yangon", re: /\byangon\b/i },
        { id: "mandalay", label: "Mandalay", re: /\bmandalay\b/i },
        { id: "naypyitaw", label: "Naypyitaw", re: /\bnay\s*pyi\s*taw|naypyitaw|naypitaw\b/i },
        { id: "sagaing", label: "Sagaing", re: /\bsagaing\b/i },
        { id: "bago", label: "Bago", re: /\bbago\b/i },
        { id: "magway", label: "Magway", re: /\bmagway\b/i },
        { id: "ayeyarwady", label: "Ayeyarwady", re: /\bayeyarwady|ayeyarwaddy|irrawaddy\b/i },
        { id: "tanintharyi", label: "Tanintharyi", re: /\btanintharyi|taninthayi\b/i },
        { id: "shan", label: "Shan", re: /\bshan\b|taunggyi|lashio|kyaing\s*tong|panglong/i },
        { id: "mon", label: "Mon", re: /\bmon state\b|\bmawlamyine\b|\bthaton\b/i },
        { id: "kayin", label: "Kayin", re: /\bkayin\b|hpa-?an\b/i },
        { id: "kachin", label: "Kachin", re: /\bkachin\b|myitkyina|banmaw|bamaw|mohnyin\b/i },
        { id: "rakhine", label: "Rakhine", re: /\brakhine\b|sittwe|kyauk\s*phyu|taunggoke\b/i },
        { id: "chin", label: "Chin", re: /\bchin state\b|\bhakha\b|\bhahka\b/i },
        { id: "kayah", label: "Kayah", re: /\bkayah\b|loikaw\b/i },
    ];

    const SET_CODES = {
        STEAMS1: ["myan", "eng", "math", "phy", "chem", "bio"],
        STEAMS2: ["myan", "eng", "math", "phy", "chem", "eco"],
        STAMS1: ["myan", "eng", "math", "hist", "geo", "eco"],
        STAMS2: ["myan", "eng", "math", "eco", "customMyan", "social"],
    };

    const universities = window.unifitAdmissions;
    const checkUniversity = window.checkUniversity;
    const STORAGE_KEY = "unifit.search.v1";
    let lastResultGroups = [];
    let lastMarksTotal = 0;
    let suppressFilterSave = false;
    let didRestore = false;

    function showFormError(message, field) {
        const box = document.getElementById("form-error");
        if (box) {
            box.hidden = false;
            box.textContent = message;
        }
        document.querySelectorAll("#generated-subjects input[aria-invalid='true']").forEach((input) => {
            input.removeAttribute("aria-invalid");
        });
        if (field) {
            field.setAttribute("aria-invalid", "true");
            field.setAttribute("aria-describedby", "form-error");
            field.focus();
        }
    }

    function clearFormError() {
        const box = document.getElementById("form-error");
        if (box) {
            box.hidden = true;
            box.textContent = "";
        }
        document.querySelectorAll("#generated-subjects input[aria-invalid='true']").forEach((input) => {
            input.removeAttribute("aria-invalid");
            input.removeAttribute("aria-describedby");
        });
    }

    function readFilters() {
        return {
            name: document.getElementById("filter-name")?.value || "",
            region: document.getElementById("filter-region")?.value || "",
            type: document.getElementById("filter-type")?.value || "",
            subjectSet: document.getElementById("filter-subject-set")?.value || "",
            sort: document.getElementById("filter-sort")?.value || "default",
        };
    }

    function writeFilters(filters) {
        if (!filters) return;
        const name = document.getElementById("filter-name");
        const region = document.getElementById("filter-region");
        const type = document.getElementById("filter-type");
        const subjectSet = document.getElementById("filter-subject-set");
        const sort = document.getElementById("filter-sort");
        if (name) name.value = filters.name || "";
        if (region && [...region.options].some((o) => o.value === filters.region)) {
            region.value = filters.region || "";
        }
        if (type && [...type.options].some((o) => o.value === filters.type)) {
            type.value = filters.type || "";
        }
        if (subjectSet) subjectSet.value = filters.subjectSet || "";
        if (sort) sort.value = filters.sort || "default";
    }

    function loadSearchState() {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            const state = JSON.parse(raw);
            if (!state || state.version !== 1 || !state.subjectSet || !state.marks) return null;
            if (!subjectSets[state.subjectSet]) return null;
            return state;
        } catch {
            return null;
        }
    }

    function saveSearchState(extra = {}) {
        const selectedSet = document.getElementById("subject-set")?.value;
        if (!selectedSet || !subjectSets[selectedSet]) return;

        const marks = {};
        for (const sub of subjectSets[selectedSet]) {
            const field = document.getElementById(sub.code);
            if (!field || field.value.trim() === "") return;
            const num = Number(field.value);
            if (Number.isNaN(num)) return;
            marks[sub.code] = num;
        }

        const state = {
            version: 1,
            active: true,
            subjectSet: selectedSet,
            marks,
            testCenter: document.getElementById("division-select")?.value || "",
            filters: readFilters(),
            matchCount: lastResultGroups.length,
            total: lastMarksTotal || Object.values(marks).reduce((a, b) => a + b, 0),
            savedAt: Date.now(),
            ...extra,
        };

        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch {
            /* ignore quota / private mode */
        }
    }

    function detailHref(url) {
        const raw = String(url || "");
        const hashIndex = raw.indexOf("#");
        const pathPart = hashIndex >= 0 ? raw.slice(0, hashIndex) : raw;
        const hash = hashIndex >= 0 ? raw.slice(hashIndex) : "";
        const joiner = pathPart.includes("?") ? "&" : "?";
        return `${pathPart}${joiner}from=search${hash}`;
    }

    function showRestoreNotice(matchCount) {
        const host = document.querySelector(".search-main");
        if (!host || document.getElementById("search-restore-notice")) return;
        const note = document.createElement("div");
        note.id = "search-restore-notice";
        note.className = "search-restore-notice";
        note.setAttribute("role", "status");

        const icon = document.createElement("i");
        icon.className = "fas fa-rotate-left";
        icon.setAttribute("aria-hidden", "true");

        const text = document.createElement("span");
        text.textContent = `Restored your previous search${
            Number.isFinite(matchCount) ? ` · ${matchCount} matches` : ""
        }.`;

        const dismiss = document.createElement("button");
        dismiss.type = "button";
        dismiss.className = "search-restore-dismiss";
        dismiss.setAttribute("aria-label", "Dismiss restore notice");
        dismiss.innerHTML = '<i class="fas fa-xmark" aria-hidden="true"></i>';
        dismiss.addEventListener("click", () => note.remove());

        note.append(icon, text, dismiss);
        const hero = host.querySelector(".search-hero");
        if (hero) hero.insertAdjacentElement("afterend", note);
        else host.insertAdjacentElement("afterbegin", note);
        window.setTimeout(() => {
            if (note.isConnected) note.remove();
        }, 10000);
    }

    function normalizePath(url) {
        return String(url || "")
            .split("#")[0]
            .replace(/^\.\.\//, "")
            .replace(/^\.\//, "")
            .toLowerCase();
    }

    function buildCampusIndex() {
        const map = new Map();
        const cards = Array.isArray(window.unifitCards) ? window.unifitCards : [];
        cards.forEach((card) => {
            const key = normalizePath(card.detail_url);
            if (key) map.set(key, card);
        });
        return map;
    }

    const campusIndex = buildCampusIndex();

    function campusFor(uni) {
        return campusIndex.get(normalizePath(uni.detailUrl)) || null;
    }

    function detectRegion(text) {
        const source = String(text || "");
        for (const region of REGION_PATTERNS) {
            if (region.re.test(source)) return region;
        }
        return null;
    }

    function categoryLabel(code) {
        if (!code) return "";
        if (typeof window.unifitCategoryLabel === "function") {
            return window.unifitCategoryLabel(code);
        }
        return String(code);
    }

    function setsCompatible(uni) {
        const req = uni.requiredSubjects;
        if (!req || req.length === 0) return Object.keys(SET_CODES);

        const sets = Array.isArray(req[0]) ? req : [req];
        const matches = [];

        Object.entries(SET_CODES).forEach(([setName, codes]) => {
            const ok = sets.some((needed) => {
                if (!Array.isArray(needed) || !needed.length) return true;
                return needed.every((code) => codes.includes(code));
            });
            if (ok) matches.push(setName);
        });

        return matches;
    }

    function enrichGroup(groupName, list) {
        const lead = list[0];
        const campus = campusFor(lead);
        const locationText = campus
            ? String(campus.address || "").replace(/^📍\s*/, "").replace(/\s+/g, " ").trim()
            : "";
        const region =
            detectRegion(locationText) ||
            detectRegion(campus ? campus.name : "") ||
            detectRegion(groupName) ||
            detectRegion(lead.name);

        return {
            key: groupName,
            list,
            lead,
            campus,
            title: groupName,
            image: campus && campus.image_path ? campus.image_path : "",
            location: locationText,
            regionId: region ? region.id : "",
            regionLabel: region ? region.label : "",
            typeCode: campus ? campus.categories || "" : "",
            typeLabel: campus ? categoryLabel(campus.categories) : "",
            subjectSets: setsCompatible(lead),
            isGroup: Boolean(lead.group),
        };
    }

    function updateLiveTotal() {
        const inputs = document.querySelectorAll("#generated-subjects input");
        const totalBox = document.getElementById("total-box");
        const totalScore = document.getElementById("total-score");
        if (!totalBox || !totalScore) return;

        if (!inputs.length) {
            totalBox.hidden = true;
            totalScore.textContent = "0";
            return;
        }

        let total = 0;
        let filled = 0;
        inputs.forEach((input) => {
            const value = input.value.trim();
            if (value === "") return;
            const num = Number(value);
            if (!Number.isNaN(num)) {
                total += num;
                filled += 1;
            }
        });

        totalBox.hidden = false;
        const next = String(total);
        if (totalScore.textContent !== next) {
            totalScore.classList.add("is-updating");
            totalScore.textContent = next;
            window.setTimeout(() => totalScore.classList.remove("is-updating"), 220);
        }

        if (!filled) totalScore.textContent = "0";
    }

    function generateSubjects() {
        const selectedSet = document.getElementById("subject-set").value;
        const container = document.getElementById("generated-subjects");
        const empty = document.getElementById("subjects-empty");

        container.innerHTML = "";
        clearFormError();

        if (!selectedSet) {
            if (empty) empty.hidden = false;
            updateLiveTotal();
            return;
        }

        if (empty) empty.hidden = true;

        subjectSets[selectedSet].forEach((sub) => {
            const wrap = document.createElement("div");
            wrap.className = "subject-box";

            const label = document.createElement("label");
            label.htmlFor = sub.code;
            label.textContent = sub.label;

            const input = document.createElement("input");
            input.type = "number";
            input.id = sub.code;
            input.placeholder = "40–100";
            input.min = "40";
            input.max = "100";
            input.required = true;
            input.inputMode = "numeric";
            input.addEventListener("input", updateLiveTotal);

            wrap.append(label, input);
            container.appendChild(wrap);
        });

        enableEnterJump();
        updateLiveTotal();
    }

    function enableEnterJump() {
        const inputs = document.querySelectorAll("#generated-subjects input");
        inputs.forEach((input, index) => {
            input.onkeydown = (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    if (inputs[index + 1]) inputs[index + 1].focus();
                }
            };
        });
    }

    document.getElementById("subject-set").addEventListener("change", () => {
        generateSubjects();
    });

    function resultCard(uni, className) {
        const card = document.createElement("div");
        card.className = className;

        if (className === "uni-sub-card") {
            const name = document.createElement("strong");
            name.textContent = uni.name;
            card.appendChild(name);
        }

        const scoreLabels = {
            eng: "English",
            math_eng_combo: "English + Mathematics",
            pcm_eng_combo: "Physics + Chemistry + Mathematics + English",
            pcm_bio_combo: "Physics + Chemistry + Mathematics + Biology",
            phy_math_or_chem_combo: "Physics + Mathematics or Physics + Chemistry",
        };
        const scores = [];
        if (Number.isFinite(uni.requiredTotal)) scores.push(`${uni.requiredTotal} total`);
        for (const [subject, score] of Object.entries(uni.subjectSpecific || {})) {
            if (scoreLabels[subject]) scores.push(`${score} in ${scoreLabels[subject]}`);
        }
        if (scores.length) {
            const summary = document.createElement("p");
            summary.className = "score-summary";
            summary.textContent = `Minimum: ${scores.join(uni.totalOrMathEnglish ? " or " : " · ")}`;
            card.appendChild(summary);
        }
        if (uni.confirmExamStream) {
            const note = document.createElement("p");
            note.className = "stream-note";
            note.setAttribute("role", "note");
            note.textContent = "Confirm your exam stream with the university before applying.";
            card.appendChild(note);
        }

        const detail = document.createElement("a");
        detail.className = "toggle-btn more-details";
        detail.href = detailHref(uni.detailUrl);
        detail.textContent = "More Details";
        detail.addEventListener("click", () => saveSearchState());
        card.appendChild(detail);
        return card;
    }

    function buildUniCard(entry, index) {
        const card = document.createElement("article");
        card.className = entry.isGroup ? "group-card search-result-card" : "search-result-card";
        card.style.animationDelay = `${Math.min(index, 12) * 40}ms`;
        card.dataset.name = entry.title.toLowerCase();
        card.dataset.region = entry.regionId;
        card.dataset.type = entry.typeCode;
        card.dataset.sets = entry.subjectSets.join(",");

        const top = document.createElement("div");
        top.className = "search-result-top";

        const thumb = document.createElement("div");
        thumb.className = "uni-thumb";
        if (entry.image) {
            const img = document.createElement("img");
            img.src = entry.image;
            img.alt = `${entry.title} campus`;
            img.loading = "lazy";
            img.decoding = "async";
            thumb.appendChild(img);
        } else {
            const icon = document.createElement("i");
            icon.className = "fas fa-building-columns";
            icon.setAttribute("aria-hidden", "true");
            thumb.appendChild(icon);
        }

        const copy = document.createElement("div");
        copy.className = "search-result-copy";
        const title = document.createElement("strong");
        title.textContent = entry.title;
        copy.appendChild(title);

        const meta = document.createElement("div");
        meta.className = "uni-meta";
        if (entry.regionLabel || entry.location) {
            const loc = document.createElement("span");
            loc.className = "uni-chip";
            loc.innerHTML = `<i class="fas fa-location-dot" aria-hidden="true"></i> ${
                entry.regionLabel || entry.location.split(",")[0]
            }`;
            meta.appendChild(loc);
        }
        if (entry.typeLabel) {
            const type = document.createElement("span");
            type.className = "uni-chip";
            type.innerHTML = `<i class="fas fa-graduation-cap" aria-hidden="true"></i> ${entry.typeLabel}`;
            meta.appendChild(type);
        }
        if (entry.isGroup) {
            const majors = document.createElement("span");
            majors.className = "uni-chip";
            majors.textContent = `${entry.list.length} majors`;
            meta.appendChild(majors);
        }
        if (meta.childElementCount) copy.appendChild(meta);

        top.append(thumb, copy);
        card.appendChild(top);

        if (entry.isGroup) {
            const body = document.createElement("div");
            body.className = "group-body";
            body.hidden = true;

            const bodyId = `group-majors-${index}-${String(entry.title)
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "-")
                .slice(0, 40)}`;
            body.id = bodyId;

            const header = document.createElement("div");
            header.className = "group-header";
            const spacer = document.createElement("span");
            const toggle = document.createElement("button");
            toggle.type = "button";
            toggle.className = "group-toggle";
            toggle.setAttribute("aria-expanded", "false");
            toggle.setAttribute("aria-controls", bodyId);
            toggle.textContent = `Show ${entry.list.length} majors`;
            toggle.addEventListener("click", function () {
                const open = body.hidden;
                body.hidden = !open;
                this.setAttribute("aria-expanded", String(open));
                this.textContent = open
                    ? `Hide ${entry.list.length} majors`
                    : `Show ${entry.list.length} majors`;
            });
            header.append(spacer, toggle);
            entry.list.forEach((uni) => body.appendChild(resultCard(uni, "uni-sub-card")));
            card.append(header, body);
        } else {
            const uni = entry.list[0];
            const scoreLabels = {
                eng: "English",
                math_eng_combo: "English + Mathematics",
                pcm_eng_combo: "Physics + Chemistry + Mathematics + English",
                pcm_bio_combo: "Physics + Chemistry + Mathematics + Biology",
                phy_math_or_chem_combo: "Physics + Mathematics or Physics + Chemistry",
            };
            const scores = [];
            if (Number.isFinite(uni.requiredTotal)) scores.push(`${uni.requiredTotal} total`);
            for (const [subject, score] of Object.entries(uni.subjectSpecific || {})) {
                if (scoreLabels[subject]) scores.push(`${score} in ${scoreLabels[subject]}`);
            }
            if (scores.length) {
                const summary = document.createElement("p");
                summary.className = "score-summary";
                summary.textContent = `Minimum: ${scores.join(uni.totalOrMathEnglish ? " or " : " · ")}`;
                card.appendChild(summary);
            }
            if (uni.confirmExamStream) {
                const note = document.createElement("p");
                note.className = "stream-note";
                note.setAttribute("role", "note");
                note.textContent = "Confirm your exam stream with the university before applying.";
                card.appendChild(note);
            }
            const detail = document.createElement("a");
            detail.className = "toggle-btn more-details";
            detail.href = detailHref(uni.detailUrl);
            detail.textContent = "More Details";
            detail.addEventListener("click", () => saveSearchState());
            card.appendChild(detail);
        }

        return card;
    }

    function populateFilterOptions(entries) {
        const regionSelect = document.getElementById("filter-region");
        const typeSelect = document.getElementById("filter-type");
        if (!regionSelect || !typeSelect) return;

        const regions = new Map();
        const types = new Map();
        entries.forEach((entry) => {
            if (entry.regionId) regions.set(entry.regionId, entry.regionLabel);
            if (entry.typeCode) types.set(entry.typeCode, entry.typeLabel);
        });

        const currentRegion = regionSelect.value;
        const currentType = typeSelect.value;

        regionSelect.innerHTML = '<option value="">All regions</option>';
        [...regions.entries()]
            .sort((a, b) => a[1].localeCompare(b[1]))
            .forEach(([id, label]) => {
                const opt = document.createElement("option");
                opt.value = id;
                opt.textContent = label;
                regionSelect.appendChild(opt);
            });

        typeSelect.innerHTML = '<option value="">All types</option>';
        [...types.entries()]
            .sort((a, b) => a[1].localeCompare(b[1]))
            .forEach(([id, label]) => {
                const opt = document.createElement("option");
                opt.value = id;
                opt.textContent = label;
                typeSelect.appendChild(opt);
            });

        if (regions.has(currentRegion)) regionSelect.value = currentRegion;
        if (types.has(currentType)) typeSelect.value = currentType;
    }

    function applyResultFilters() {
        const resultsDiv = document.getElementById("results");
        const nameQuery = (document.getElementById("filter-name").value || "").trim().toLowerCase();
        const region = document.getElementById("filter-region").value;
        const type = document.getElementById("filter-type").value;
        const subjectSet = document.getElementById("filter-subject-set").value;
        const sort = document.getElementById("filter-sort").value;

        let filtered = lastResultGroups.slice();

        if (nameQuery) {
            filtered = filtered.filter((entry) => entry.title.toLowerCase().includes(nameQuery));
        }
        if (region) {
            filtered = filtered.filter((entry) => entry.regionId === region);
        }
        if (type) {
            filtered = filtered.filter((entry) => entry.typeCode === type);
        }
        if (subjectSet) {
            filtered = filtered.filter((entry) => entry.subjectSets.includes(subjectSet));
        }

        if (sort === "az") {
            filtered.sort((a, b) => a.title.localeCompare(b.title));
        } else if (sort === "za") {
            filtered.sort((a, b) => b.title.localeCompare(a.title));
        }

        resultsDiv.innerHTML = "";

        if (!filtered.length) {
            const empty = document.createElement("p");
            empty.className = "results-empty";
            empty.textContent = lastResultGroups.length
                ? "No universities match these filters."
                : "No universities match your marks.";
            resultsDiv.appendChild(empty);
            return;
        }

        const container = document.createElement("div");
        container.className = "results-container";
        filtered.forEach((entry, index) => container.appendChild(buildUniCard(entry, index)));
        resultsDiv.appendChild(container);

        if (!suppressFilterSave) saveSearchState();
    }

    function clearFilters() {
        document.getElementById("filter-name").value = "";
        document.getElementById("filter-region").value = "";
        document.getElementById("filter-type").value = "";
        document.getElementById("filter-subject-set").value = "";
        document.getElementById("filter-sort").value = "default";
        applyResultFilters();
    }

    function searchUniversities(options = {}) {
        const {
            restoreFilters = null,
            skipDelay = false,
            scrollToResults = true,
            fromRestore = false,
        } = options;

        clearFormError();
        const selectedSet = document.getElementById("subject-set").value;

        if (!selectedSet) {
            showFormError("Please select a subject set first.");
            document.getElementById("subject-set").focus();
            return;
        }

        const subjectList = subjectSets[selectedSet];
        const marks = {};

        for (const sub of subjectList) {
            const field = document.getElementById(sub.code);
            const value = field.value.trim();

            if (value === "") {
                showFormError("Please fill all subject marks.", field);
                return;
            }

            const num = Number(value);
            if (Number.isNaN(num) || num < 40 || num > 100) {
                showFormError("Please enter marks between 40 and 100.", field);
                return;
            }

            marks[sub.code] = num;
        }

        marks.total = Object.values(marks).reduce((a, b) => a + b, 0);
        lastMarksTotal = marks.total;

        const spinner = document.getElementById("loading-spinner");
        const resultsPanel = document.getElementById("results-panel");
        const resultsDiv = document.getElementById("results");
        const streamBanner = document.getElementById("stream-banner");

        const searchMain = document.querySelector(".search-main");
        const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        spinner.hidden = false;
        if (searchMain) searchMain.setAttribute("aria-busy", "true");
        resultsPanel.hidden = true;
        resultsDiv.innerHTML = "";

        const run = () => {
            const testCenter = document.getElementById("division-select").value;
            const eligible = universities.filter((u) => checkUniversity(u, marks, testCenter));

            const groups = {};
            eligible.forEach((u) => {
                const key = u.group || u.name;
                if (!groups[key]) groups[key] = [];
                groups[key].push(u);
            });

            lastResultGroups = Object.entries(groups).map(([groupName, list]) =>
                enrichGroup(groupName, list)
            );

            const uniqueCount = lastResultGroups.length;
            const needsStreamConfirm = eligible.some((uni) => uni.confirmExamStream);

            document.getElementById("summary-total").textContent = String(marks.total);
            document.getElementById("summary-matches").textContent = String(uniqueCount);
            document.getElementById("total-score").textContent = String(marks.total);
            document.getElementById("total-box").hidden = false;

            if (needsStreamConfirm) {
                streamBanner.hidden = false;
                streamBanner.textContent =
                    "Some matches need you to confirm your exam stream with the campus.";
            } else {
                streamBanner.hidden = true;
                streamBanner.textContent = "";
            }

            populateFilterOptions(lastResultGroups);

            suppressFilterSave = true;
            if (restoreFilters) {
                writeFilters(restoreFilters);
                applyResultFilters();
            } else {
                clearFilters();
            }
            suppressFilterSave = false;

            saveSearchState();

            resultsPanel.hidden = false;
            spinner.hidden = true;
            if (searchMain) searchMain.removeAttribute("aria-busy");

            if (fromRestore) showRestoreNotice(uniqueCount);

            if (scrollToResults) {
                resultsPanel.scrollIntoView({
                    behavior: fromRestore || skipDelay || prefersReducedMotion ? "auto" : "smooth",
                    block: "start",
                });
            }
        };

        if (skipDelay || prefersReducedMotion) run();
        else setTimeout(run, 450);
    }

    function tryRestoreSearch() {
        if (didRestore) return false;
        if (document.getElementById("results-panel") && !document.getElementById("results-panel").hidden) {
            return false;
        }

        const state = loadSearchState();
        if (!state || !state.active) return false;

        didRestore = true;

        const subjectSelect = document.getElementById("subject-set");
        const centerSelect = document.getElementById("division-select");
        subjectSelect.value = state.subjectSet;
        generateSubjects();

        for (const sub of subjectSets[state.subjectSet]) {
            const field = document.getElementById(sub.code);
            if (field && state.marks[sub.code] != null) {
                field.value = String(state.marks[sub.code]);
            }
        }
        updateLiveTotal();

        if (centerSelect && state.testCenter) centerSelect.value = state.testCenter;

        searchUniversities({
            restoreFilters: state.filters || null,
            skipDelay: true,
            scrollToResults: true,
            fromRestore: true,
        });

        return true;
    }

    function clearSavedSearchState() {
        try {
            sessionStorage.removeItem(STORAGE_KEY);
        } catch {
            /* ignore quota / private mode */
        }
    }

    function clearForm(options = {}) {
        const { skipConfirm = false } = options;
        const resultsPanel = document.getElementById("results-panel");
        const hasResults = resultsPanel && !resultsPanel.hidden && lastResultGroups.length > 0;
        if (!skipConfirm && hasResults) {
            const ok = window.confirm(
                "Reset will clear your marks, results, and saved search so you can start a new one. Continue?"
            );
            if (!ok) return;
        }

        const subjectSelect = document.getElementById("subject-set");
        const centerSelect = document.getElementById("division-select");
        const resultsDiv = document.getElementById("results");
        const spinner = document.getElementById("loading-spinner");
        const streamBanner = document.getElementById("stream-banner");
        const summaryTotal = document.getElementById("summary-total");
        const summaryMatches = document.getElementById("summary-matches");
        const restoreNotice = document.getElementById("search-restore-notice");
        const searchMain = document.querySelector(".search-main");

        if (subjectSelect) subjectSelect.value = "";
        if (centerSelect) centerSelect.selectedIndex = 0;
        generateSubjects();

        lastResultGroups = [];
        lastMarksTotal = 0;
        didRestore = false;
        clearSavedSearchState();

        if (spinner) spinner.hidden = true;
        if (searchMain) searchMain.removeAttribute("aria-busy");
        if (resultsPanel) resultsPanel.hidden = true;
        if (resultsDiv) resultsDiv.innerHTML = "";
        if (streamBanner) {
            streamBanner.hidden = true;
            streamBanner.textContent = "";
        }
        if (summaryTotal) summaryTotal.textContent = "0";
        if (summaryMatches) summaryMatches.textContent = "0";
        if (restoreNotice) restoreNotice.remove();

        const filterName = document.getElementById("filter-name");
        const filterRegion = document.getElementById("filter-region");
        const filterType = document.getElementById("filter-type");
        const filterSubjectSet = document.getElementById("filter-subject-set");
        const filterSort = document.getElementById("filter-sort");
        if (filterName) filterName.value = "";
        if (filterRegion) filterRegion.innerHTML = '<option value="">All regions</option>';
        if (filterType) filterType.innerHTML = '<option value="">All types</option>';
        if (filterSubjectSet) filterSubjectSet.value = "";
        if (filterSort) filterSort.value = "default";

        clearFormError();
        updateLiveTotal();

        if (subjectSelect) subjectSelect.focus();
    }

    ["filter-name", "filter-region", "filter-type", "filter-subject-set", "filter-sort"].forEach(
        (id) => {
            const el = document.getElementById(id);
            if (!el) return;
            const eventName = el.tagName === "INPUT" ? "input" : "change";
            el.addEventListener(eventName, applyResultFilters);
        }
    );

    const clearBtn = document.getElementById("clear-filters");
    if (clearBtn) clearBtn.addEventListener("click", clearFilters);

    const resetBtn = document.getElementById("reset-search");
    if (resetBtn) resetBtn.addEventListener("click", () => clearForm());

    const runSearchBtn = document.getElementById("run-search");
    if (runSearchBtn) runSearchBtn.addEventListener("click", () => searchUniversities());

    const backToTop = document.getElementById("backToTop");
    if (backToTop) {
        window.addEventListener(
            "scroll",
            () => {
                const show =
                    document.body.scrollTop > 200 || document.documentElement.scrollTop > 200;
                backToTop.style.display = show ? "block" : "none";
            },
            { passive: true }
        );
        backToTop.addEventListener("click", () => {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    tryRestoreSearch();
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) {
            didRestore = false;
            tryRestoreSearch();
        }
    });

    window.generateSubjects = generateSubjects;
    window.searchUniversities = searchUniversities;
    window.clearForm = clearForm;
})();
