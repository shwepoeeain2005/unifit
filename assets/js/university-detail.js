(() => {
    const detail = window.unifitDetail ?? { sections: window.unifitSections };
    const { campus, sections, admissions } = detail;
    const detailScriptSrc =
        document.currentScript?.src ||
        new URL("../assets/js/university-detail.js", window.location.href).href;
    const majors = document.querySelector("fieldset[data-unifit-majors]");
    if (!majors) {
        throw new Error("UniFit detail page is missing fieldset[data-unifit-majors].");
    }
    if (!Array.isArray(sections) || sections.length === 0) {
        throw new Error("UniFit detail data does not match this page.");
    }

    const CATEGORY_LABELS = {
        medicine: "Medicine",
        tu: "TU",
        cu: "CU",
        pu: "PU",
        "Art&science": "Art & Science",
        eco: "Economics",
        foreign: "Foreign Language",
        Management: "Management",
        art: "Art & Culture",
        maritime: "Maritime",
        Aerospace: "Aerospace",
        Education: "Education",
        agriculture: "Agriculture",
    };

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function ensureFonts() {
        if (document.querySelector('link[href*="Noto+Sans+Myanmar"]')) return;
        const preconnectA = document.createElement("link");
        preconnectA.rel = "preconnect";
        preconnectA.href = "https://fonts.googleapis.com";
        const preconnectB = document.createElement("link");
        preconnectB.rel = "preconnect";
        preconnectB.href = "https://fonts.gstatic.com";
        preconnectB.crossOrigin = "anonymous";
        const fonts = document.createElement("link");
        fonts.rel = "stylesheet";
        fonts.href =
            "https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@400;600;700&family=Quicksand:wght@400;500;600;700&display=swap";
        document.head.append(preconnectA, preconnectB, fonts);
    }

    function loadScript(src) {
        return new Promise((resolve, reject) => {
            if ([...document.scripts].some((s) => (s.src || "").includes(src.replace(/^\.\.\//, "")))) {
                resolve();
                return;
            }
            const script = document.createElement("script");
            script.src = src;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error(`Failed to load ${src}`));
            document.head.appendChild(script);
        });
    }

    function cleanAddress(address) {
        return String(address || "")
            .replace(/^📍\s*/u, "")
            .replace(/\s*📍\s*$/u, "")
            .replace(/\s+/g, " ")
            .trim();
    }

    function categoryLabel(key) {
        return CATEGORY_LABELS[key] || key || "University";
    }

    function currentDetailUrl() {
        const file = (location.pathname.split("/").pop() || "").split("?")[0];
        return file ? `universities/${file}` : "";
    }

    function findCard() {
        const cards = window.unifitCards;
        if (!Array.isArray(cards)) return null;
        const detailUrl = currentDetailUrl();
        const byUrl = cards.find((c) => c.detail_url === detailUrl);
        if (byUrl) return byUrl;
        const name = campus?.name || document.querySelector("[data-unifit-name]")?.textContent?.trim();
        if (!name) return null;
        return cards.find((c) => c.name === name) || null;
    }

    function sectionIcon(title) {
        const t = String(title || "");
        if (/website/i.test(t)) return "fa-globe";
        if (/intern|အလုပ်သင်/i.test(t)) return "fa-briefcase-medical";
        if (/m5|ပဉ္စမ|fifth year/i.test(t)) return "fa-notes-medical";
        if (/m4|စတုတ္ထ|fourth year/i.test(t)) return "fa-user-doctor";
        if (/year\s*3|တတိယ|third year/i.test(t)) return "fa-hospital";
        if (/year\s*1|year\s*2|first|second|အခြေခံနှစ်/i.test(t)) return "fa-book-medical";
        if (/mbbs|admission|အချက်အလက်|ရည်ရွယ်/i.test(t)) return "fa-stethoscope";
        if (/major|subject|course|သင်ရိုး/i.test(t)) return "fa-graduation-cap";
        if (/pharmacy|ဆေးဝါး/i.test(t)) return "fa-pills";
        if (/nursing|သူနာပြု/i.test(t)) return "fa-user-nurse";
        if (/dental|သွား/i.test(t)) return "fa-tooth";
        if (/engineer|technolog/i.test(t)) return "fa-gears";
        return "fa-layer-group";
    }

    function extractWebsite(section) {
        const template = document.createElement("template");
        template.innerHTML = section.html || "";
        const anchor = template.content.querySelector("a[href]");
        if (!anchor) return null;
        return {
            href: anchor.getAttribute("href")?.trim() || "",
            label: (anchor.textContent || "").trim() || campus?.name || "Official Website",
        };
    }

    function firstMeaningfulText(html) {
        const template = document.createElement("template");
        template.innerHTML = html || "";
        const paragraphs = [...template.content.querySelectorAll("p")];
        for (const p of paragraphs) {
            const text = (p.textContent || "").replace(/\s+/g, " ").trim();
            if (text.length > 40) return text.slice(0, 220) + (text.length > 220 ? "…" : "");
        }
        return "";
    }

    function resolveImagePath(path) {
        if (!path) return "";
        if (/^(https?:|data:|\/)/i.test(path)) return path;
        if (path.startsWith("../")) return path;
        if (path.startsWith("assets/")) return `../${path}`;
        return path;
    }

    function hydrateImages(root, images) {
        root.querySelectorAll("img[src]").forEach((image, position) => {
            const record = images?.[position];
            if (record) {
                image.setAttribute("src", record.image_path);
                if (record.alt_text === null) image.removeAttribute("alt");
                else image.setAttribute("alt", record.alt_text || "");
            }
            image.setAttribute("loading", "lazy");
            image.setAttribute("decoding", "async");
        });
        root.querySelectorAll(".accordion-content").forEach((node) => {
            node.setAttribute("lang", "my");
        });
    }

    function createEl(tag, className, text) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text != null) el.textContent = text;
        return el;
    }

    function buildHero(card, legendText, introText) {
        const hero = createEl("section", "uni-hero");
        hero.setAttribute("aria-label", "University profile");

        const media = createEl("div", "uni-hero-media");
        const img = document.createElement("img");
        img.className = "uni-hero-image";
        img.alt = campus?.name || card?.name || "University campus";
        img.decoding = "async";
        const src = resolveImagePath(card?.image_path);
        if (src) {
            img.src = src;
        } else {
            img.removeAttribute("src");
            media.classList.add("uni-hero-media--fallback");
        }
        media.appendChild(img);
        media.appendChild(createEl("div", "uni-hero-scrim"));

        const content = createEl("div", "uni-hero-content");
        const back = document.createElement("a");
        back.href = "../unilists.html";
        back.className = "uni-back-btn";
        back.innerHTML = '<i class="fas fa-arrow-left" aria-hidden="true"></i><span>Back to Universities</span>';

        const badgeRow = createEl("div", "uni-hero-badges");
        if (card?.categories) {
            const badge = createEl("span", "uni-category-badge", categoryLabel(card.categories));
            badgeRow.appendChild(badge);
        }
        if (legendText) {
            const programBadge = createEl("span", "uni-program-badge", legendText);
            badgeRow.appendChild(programBadge);
        }

        const title = createEl("h1", "uni-hero-title");
        title.setAttribute("data-unifit-name", "");
        title.textContent = campus?.name || card?.name || document.title || "University";

        const location = createEl("p", "uni-hero-location");
        location.setAttribute("data-unifit-address", "");
        const locIcon = document.createElement("i");
        locIcon.className = "fas fa-location-dot";
        locIcon.setAttribute("aria-hidden", "true");
        const locText = createEl("span", "", cleanAddress(campus?.address || card?.address || "") || "Myanmar");
        location.append(locIcon, locText);

        content.append(back, badgeRow, title, location);

        if (introText) {
            const intro = createEl("p", "uni-hero-intro", introText);
            intro.lang = "my";
            content.appendChild(intro);
        }

        const actions = createEl("div", "uni-hero-actions");
        const explore = document.createElement("a");
        explore.href = "#academic-programs";
        explore.className = "uni-btn uni-btn-primary";
        explore.innerHTML = '<i class="fas fa-book-open" aria-hidden="true"></i><span>Explore Programs</span>';
        actions.appendChild(explore);

        const websiteSection = sections.find((s) => /^website link$/i.test((s.title || "").trim()));
        const website = websiteSection ? extractWebsite(websiteSection) : null;
        if (website?.href) {
            const visit = document.createElement("a");
            visit.href = website.href;
            visit.target = "_blank";
            visit.rel = "noopener noreferrer";
            visit.className = "uni-btn uni-btn-ghost";
            visit.innerHTML = '<i class="fas fa-arrow-up-right-from-square" aria-hidden="true"></i><span>Visit Website</span>';
            actions.appendChild(visit);
        }
        content.appendChild(actions);

        hero.append(media, content);
        return { hero, website };
    }

    function websiteHost(href) {
        try {
            const url = new URL(href);
            const host = url.host.replace(/^www\./i, "");
            const path = url.pathname === "/" ? "" : url.pathname.replace(/\/$/, "");
            return `${host}${path}`;
        } catch {
            return String(href || "").replace(/^https?:\/\/(www\.)?/i, "").replace(/\/$/, "");
        }
    }

    function buildOverview(card, programCount, website) {
        const section = createEl("section", "uni-overview");
        section.setAttribute("aria-label", "University information");

        const inner = createEl("div", "uni-section-inner uni-overview-inner");
        const heading = createEl("div", "uni-section-heading uni-overview-heading");
        heading.append(
            createEl("h2", "", "University Overview"),
            createEl("p", "uni-section-subtitle", "Key facts drawn from UniFit campus data.")
        );
        inner.appendChild(heading);

        const grid = createEl("div", "uni-info-grid");
        const items = [];

        const address = cleanAddress(campus?.address || card?.address || "");
        if (address) {
            items.push({
                kind: "location",
                icon: "fa-location-dot",
                label: "Location",
                value: address,
            });
        }
        if (card?.categories) {
            items.push({
                kind: "type",
                icon: "fa-building-columns",
                label: "University Type",
                value: categoryLabel(card.categories),
            });
        }
        if (programCount > 0) {
            items.push({
                kind: "programs",
                icon: "fa-layer-group",
                label: "Available Programs",
                value: String(programCount),
                support: programCount === 1 ? "information section" : "information sections",
            });
        }
        if (website?.href) {
            items.push({
                kind: "website",
                icon: "fa-globe",
                label: "Official Website",
                value: websiteHost(website.href),
                href: website.href,
            });
        }

        items.forEach((item, index) => {
            const cardEl = createEl("article", `uni-info-card uni-info-card--${item.kind}`);
            cardEl.style.setProperty("--stagger", String(index));

            const iconWrap = createEl("div", "uni-info-icon");
            iconWrap.innerHTML = `<i class="fas ${item.icon}" aria-hidden="true"></i>`;

            const body = createEl("div", "uni-info-body");
            body.appendChild(createEl("span", "uni-info-label", item.label));

            if (item.kind === "programs") {
                body.appendChild(createEl("p", "uni-info-value uni-info-value--stat", item.value));
                body.appendChild(createEl("span", "uni-info-support", item.support));
            } else if (item.kind === "type") {
                body.appendChild(createEl("p", "uni-info-value uni-info-value--type", item.value));
            } else if (item.kind === "website" && item.href) {
                body.appendChild(createEl("p", "uni-info-value uni-info-host", item.value));
                const visit = document.createElement("a");
                visit.href = item.href;
                visit.target = "_blank";
                visit.rel = "noopener noreferrer";
                visit.className = "uni-info-visit";
                visit.innerHTML = '<span>Visit Website</span><i class="fas fa-arrow-up-right-from-square" aria-hidden="true"></i>';
                body.appendChild(visit);
            } else {
                body.appendChild(createEl("p", "uni-info-value", item.value));
            }

            cardEl.append(iconWrap, body);
            grid.appendChild(cardEl);
        });

        if (!items.length) return null;
        inner.appendChild(grid);
        section.appendChild(inner);
        return section;
    }

    function buildAccordion(section) {
        const accordion = createEl("div", "accordion");

        const header = document.createElement("button");
        header.type = "button";
        header.className = "accordion-header";
        header.setAttribute("aria-expanded", "false");

        const left = createEl("span", "accordion-header-main");
        const icon = createEl("span", "accordion-icon");
        icon.innerHTML = `<i class="fas ${sectionIcon(section.title)}" aria-hidden="true"></i>`;
        const textWrap = createEl("span", "accordion-text");
        textWrap.appendChild(createEl("span", "accordion-title", section.title || ""));
        left.append(icon, textWrap);

        const arrow = createEl("span", "arrow");
        arrow.innerHTML = '<i class="fas fa-chevron-down" aria-hidden="true"></i>';
        header.append(left, arrow);

        const template = document.createElement("template");
        template.innerHTML = section.html;
        hydrateImages(template.content, section.images);

        const collapse = createEl("div", "accordion-collapse");
        collapse.setAttribute("aria-hidden", "true");
        collapse.append(template.content);

        header.addEventListener("click", () => {
            const open = accordion.classList.toggle("open");
            header.setAttribute("aria-expanded", String(open));
            collapse.setAttribute("aria-hidden", String(!open));
        });

        accordion.append(header, collapse);
        return accordion;
    }

    function buildWebsiteCard(website) {
        if (!website?.href) return null;
        const section = createEl("section", "uni-website");
        const inner = createEl("div", "uni-section-inner");
        const card = createEl("article", "uni-website-card");

        const icon = createEl("div", "uni-website-icon");
        icon.innerHTML = '<i class="fas fa-globe" aria-hidden="true"></i>';

        const body = createEl("div", "uni-website-body");
        body.append(
            createEl("span", "uni-website-label", "Official Website"),
            createEl("p", "uni-website-url", website.href)
        );

        const btn = document.createElement("a");
        btn.href = website.href;
        btn.target = "_blank";
        btn.rel = "noopener noreferrer";
        btn.className = "uni-btn uni-btn-primary";
        btn.innerHTML = '<i class="fas fa-arrow-up-right-from-square" aria-hidden="true"></i><span>Visit Website</span>';

        card.append(icon, body, btn);
        inner.appendChild(card);
        section.appendChild(inner);
        return section;
    }

    function setupReveal() {
        if (prefersReducedMotion) {
            document.querySelectorAll("[data-reveal]").forEach((el) => el.classList.add("is-visible"));
            return;
        }
        const nodes = document.querySelectorAll("[data-reveal]");
        if (!("IntersectionObserver" in window) || !nodes.length) {
            nodes.forEach((el) => el.classList.add("is-visible"));
            return;
        }
        const observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (!entry.isIntersecting) continue;
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            },
            { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
        );
        nodes.forEach((el) => observer.observe(el));
    }

    function addRules(parent, rules) {
        for (const rule of rules) {
            const line = document.createElement("p");
            line.lang = "my";
            line.innerHTML = rule;
            parent.appendChild(line);
        }
    }

    function renderAdmissions(anchor) {
        if (!admissions) return;

        const stylesheet = document.createElement("link");
        stylesheet.rel = "stylesheet";
        stylesheet.href = new URL("../css/university-admissions.css?v=2026-detail-ui-1", detailScriptSrc).href;
        document.head.appendChild(stylesheet);

        const box = document.createElement("section");
        box.className = "university-admissions";
        box.id = "admission-requirements";
        box.tabIndex = -1;
        box.setAttribute("data-reveal", "");

        const heading = document.createElement("h2");
        heading.textContent = "2026 Admission Requirements";
        box.appendChild(heading);

        if (!admissions.shared.length && !admissions.programmes.length) {
            const note = document.createElement("p");
            note.className = "unverified-note";
            note.textContent = "2026 admissions are awaiting confirmation.";
            box.appendChild(note);
        }

        addRules(box, admissions.shared);
        for (const programme of admissions.programmes) {
            const section = document.createElement("div");
            section.className = "programme-requirements";
            section.id = programme.id;
            section.tabIndex = -1;
            const title = document.createElement("h3");
            title.textContent = programme.names.join(" · ");
            section.appendChild(title);
            addRules(section, programme.rules);
            box.appendChild(section);
        }

        anchor.after(box);

        function jumpToRequirements() {
            const target = document.getElementById(location.hash.slice(1));
            if (target && box.contains(target)) {
                target.focus({ preventScroll: true });
                target.scrollIntoView({ block: "start" });
            }
        }

        window.addEventListener("hashchange", jumpToRequirements);
        if (stylesheet.sheet) jumpToRequirements();
        else stylesheet.addEventListener("load", jumpToRequirements, { once: true });
    }

    async function boot() {
        ensureFonts();
        if (document.body) document.body.classList.add("uni-detail");
        else document.documentElement.classList.add("uni-detail");

        try {
            if (!window.unifitCards) {
                await loadScript("../data/universities.js");
            }
        } catch {
            /* Card metadata is optional enrichment */
        }

        const card = findCard();
        const legend = majors.querySelector("legend");
        const legendText = legend ? legend.textContent.trim() : "";

        if (campus) {
            const title = document.querySelector("[data-unifit-name]");
            const address = document.querySelector("[data-unifit-address]");
            if (title) title.textContent = campus.name;
            if (address) address.textContent = campus.address;
            if (campus.name) document.title = campus.name;
        }

        const contentSections = [];
        let websiteMeta = null;
        for (const section of sections) {
            if (/^website link$/i.test((section.title || "").trim())) {
                websiteMeta = extractWebsite(section);
                continue;
            }
            contentSections.push(section);
        }

        // Only show a hero intro when the page legend is a curriculum overview
        // (not a generic "Available Majors" label), to avoid using a major blurb
        // as the university description.
        const overviewLegend = legendText && !/^available\b/i.test(legendText);
        const introText = overviewLegend && contentSections[0]
            ? firstMeaningfulText(contentSections[0].html)
            : "";

        const { hero, website } = buildHero(card, legendText, introText);
        const effectiveWebsite = websiteMeta || website;

        const overview = buildOverview(card, contentSections.length, effectiveWebsite);

        for (const child of [...majors.children]) {
            if (child.tagName !== "LEGEND") child.remove();
        }

        if (legend) {
            legend.classList.add("uni-legend");
            legend.textContent = legendText || "Academic Programs";
        }

        for (const section of contentSections) {
            majors.appendChild(buildAccordion(section));
        }

        const oldHome = document.querySelector("a.home-btn");
        const oldHeader = document.querySelector(".header");
        const footer = document.querySelector("footer");

        if (oldHome) oldHome.remove();
        if (oldHeader) oldHeader.remove();

        // Detach majors from the original shell before placing it in the new layout.
        majors.remove();

        const academic = createEl("section", "uni-academic");
        academic.id = "academic-programs";
        academic.setAttribute("aria-label", "Academic programs and requirements");
        const academicInner = createEl("div", "uni-section-inner");
        const academicHeading = createEl("div", "uni-section-heading");
        academicHeading.append(
            createEl("h2", "", "Academic Programs & Requirements"),
            createEl(
                "p",
                "uni-section-subtitle",
                "Expand each stage to explore curriculum details, learning outcomes, and supporting materials."
            )
        );
        academicInner.append(academicHeading, majors);
        academic.appendChild(academicInner);

        const websiteCard = buildWebsiteCard(effectiveWebsite);

        const page = createEl("main", "uni-detail-page");
        page.appendChild(hero);
        if (overview) {
            overview.setAttribute("data-reveal", "");
            page.appendChild(overview);
        }
        academic.setAttribute("data-reveal", "");
        page.appendChild(academic);
        if (websiteCard) {
            websiteCard.setAttribute("data-reveal", "");
            page.appendChild(websiteCard);
        }

        if (footer) footer.before(page);
        else document.body.appendChild(page);

        renderAdmissions(websiteCard || academic);
        setupReveal();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            boot().catch((err) => console.error(err));
        }, { once: true });
    } else {
        boot().catch((err) => console.error(err));
    }
})();
