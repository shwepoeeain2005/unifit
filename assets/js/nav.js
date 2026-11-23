(() => {
    const nav = document.querySelector("nav.links");
    if (!nav) return;

    const hamburger = document.getElementById("hamburger") || nav.querySelector(".hamburger, .menu-toggle");
    const navLinks = document.getElementById("navLinks") || nav.querySelector(".nav-links");
    const logo = nav.querySelector(".logo");
    const ctaLinks = nav.querySelectorAll(".nav-cta");

    const ICON_MAP = {
        "index.html": "fa-house",
        "unilists.html": "fa-building-columns",
        "req1.html": "fa-clipboard-list",
        "requirement.html": "fa-clipboard-list",
        "formeq.html": "fa-clipboard-list",
        "aboutus.html": "fa-users",
        "search.html": "fa-magnifying-glass",
    };

    const SHORT_LABEL = {
        "index.html": "Home",
        "unilists.html": "Lists",
        "req1.html": "Requirements",
        "aboutus.html": "About",
        "search.html": "Search",
    };

    function pageFile() {
        const parts = window.location.pathname.split("/").filter(Boolean);
        return (parts[parts.length - 1] || "index.html").toLowerCase();
    }

    function inUniversities() {
        return /\/universities(\/|$)/i.test(window.location.pathname);
    }

    function normalizeHref(href) {
        if (!href) return "";
        try {
            return (new URL(href, window.location.href).pathname.split("/").pop() || "").toLowerCase();
        } catch {
            return String(href).split("/").pop().toLowerCase() || "";
        }
    }

    function enhanceLogoText() {
        if (!logo) return;
        const text = logo.querySelector(".logo-text");
        if (!text || text.querySelector(".logo-fit")) return;
        if (text.childElementCount > 0) return;
        const raw = (text.textContent || "").trim();
        if (/^unifit$/i.test(raw)) {
            text.innerHTML = '<span class="logo-uni">Uni</span><span class="logo-fit">Fit</span>';
        }
    }

    function enhanceNavIcons() {
        if (!navLinks) return;
        navLinks.querySelectorAll("a[href]:not(.nav-cta)").forEach((link) => {
            if (link.querySelector(".nav-ico")) return;

            const file = normalizeHref(link.getAttribute("href"));
            const iconClass = ICON_MAP[file] || "fa-circle";
            const fullLabel = (link.textContent || "").trim();
            const shortLabel = SHORT_LABEL[file] || fullLabel;

            const icon = document.createElement("i");
            icon.className = `fas ${iconClass} nav-ico`;
            icon.setAttribute("aria-hidden", "true");

            const fullSpan = document.createElement("span");
            fullSpan.className = "nav-link-label-full";
            fullSpan.textContent = fullLabel;

            const shortSpan = document.createElement("span");
            shortSpan.className = "nav-link-label-short";
            shortSpan.textContent = shortLabel;

            link.textContent = "";
            link.append(icon, fullSpan, shortSpan);
        });
    }

    function enhanceSearchCta() {
        nav.querySelectorAll(".nav-cta").forEach((link) => {
            if (link.querySelector(".nav-cta-field")) return;

            const field = document.createElement("span");
            field.className = "nav-cta-field";

            let icon = link.querySelector("i");
            if (!icon) {
                icon = document.createElement("i");
                icon.className = "fas fa-magnifying-glass";
                icon.setAttribute("aria-hidden", "true");
            } else {
                icon = icon.cloneNode(true);
            }

            field.appendChild(icon);

            const label = document.createElement("span");
            label.className = "nav-cta-label";
            label.textContent = "Search";

            link.textContent = "";
            link.append(field, label);
            if (!link.getAttribute("aria-label")) {
                link.setAttribute("aria-label", "Search Your Uni");
            }
        });
    }

    function setActiveLink() {
        const current = pageFile();
        const uniDetail = inUniversities();
        const reqPages = new Set(["req1.html", "requirement.html", "formeq.html"]);
        const links = nav.querySelectorAll(".nav-links a[href]:not(.nav-cta), .nav-cta");

        links.forEach((link) => {
            const file = normalizeHref(link.getAttribute("href"));
            let active = false;

            if (link.classList.contains("nav-cta")) {
                active = file === "search.html" && current === "search.html";
            } else if (uniDetail) {
                active = file === "unilists.html";
            } else if (!current || current === "index.html") {
                active = file === "index.html";
            } else if (reqPages.has(current)) {
                active = file === "req1.html";
            } else {
                active = file === current;
            }

            link.classList.toggle("active", active);
            if (active) link.setAttribute("aria-current", "page");
            else link.removeAttribute("aria-current");
        });
    }

    function setMenuOpen(open) {
        if (!navLinks) return;
        navLinks.classList.toggle("show", open);
        nav.classList.toggle("is-open", open);
        if (hamburger) {
            hamburger.setAttribute("aria-expanded", open ? "true" : "false");
            const icon = hamburger.querySelector("i");
            if (icon) {
                icon.classList.toggle("fa-bars", !open);
                icon.classList.toggle("fa-xmark", open);
            }
        }
        document.body.style.overflow = open ? "hidden" : "";
    }

    function isMenuOpen() {
        return Boolean(navLinks && navLinks.classList.contains("show"));
    }

    if (hamburger && navLinks) {
        if (!hamburger.hasAttribute("aria-label")) {
            hamburger.setAttribute("aria-label", "Toggle navigation menu");
        }
        hamburger.setAttribute("aria-controls", navLinks.id || "navLinks");
        hamburger.setAttribute("aria-expanded", "false");

        const toggle = (event) => {
            event.preventDefault();
            setMenuOpen(!isMenuOpen());
        };

        hamburger.addEventListener("click", toggle);

        navLinks.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => setMenuOpen(false));
        });
        ctaLinks.forEach((link) => {
            link.addEventListener("click", () => setMenuOpen(false));
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && isMenuOpen()) setMenuOpen(false);
        });

        document.addEventListener("click", (event) => {
            if (!isMenuOpen()) return;
            if (nav.contains(event.target)) return;
            setMenuOpen(false);
        });

        window.addEventListener("resize", () => {
            if (window.innerWidth > 860 && isMenuOpen()) setMenuOpen(false);
        });
    }

    const onScroll = () => {
        nav.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    if (logo) {
        const tag = logo.tagName.toLowerCase();
        if (tag !== "a") {
            logo.setAttribute("role", "link");
            logo.setAttribute("tabindex", "0");
            if (!logo.getAttribute("aria-label")) {
                logo.setAttribute("aria-label", "UniFit home");
            }
            const goHome = () => {
                window.location.href = inUniversities() ? "../index.html" : "index.html";
            };
            logo.addEventListener("click", goHome);
            logo.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    goHome();
                }
            });
        }
    }

    function pathPrefix() {
        return inUniversities() ? "../" : "";
    }

    function universityLabel() {
        const h1 = document.querySelector("main h1, .header h1, h1");
        if (h1) {
            const text = (h1.textContent || "").replace(/\s+/g, " ").trim();
            if (text) return text;
        }
        return (document.title || "University")
            .replace(/\s*[|\-–].*$/, "")
            .replace(/\s+/g, " ")
            .trim() || "University";
    }

    function loadSearchReturnState() {
        try {
            const state = JSON.parse(sessionStorage.getItem("unifit.search.v1") || "null");
            if (!state || state.version !== 1 || !state.active || !state.subjectSet) return null;
            return state;
        } catch {
            return null;
        }
    }

    function cameFromSearch() {
        return new URLSearchParams(window.location.search).get("from") === "search";
    }

    function breadcrumbTrail() {
        const file = pageFile();
        const p = pathPrefix();
        const home = { label: "Home", href: `${p}index.html` };

        if (!file || file === "index.html") return null;

        if (inUniversities()) {
            if (cameFromSearch() && loadSearchReturnState()) {
                return [
                    home,
                    { label: "Search Results", href: `${p}search.html` },
                    { label: universityLabel() },
                ];
            }
            return [
                home,
                { label: "University Lists", href: `${p}unilists.html` },
                { label: universityLabel() },
            ];
        }

        const map = {
            "unilists.html": [home, { label: "University Lists" }],
            "search.html": [home, { label: "Search Your Uni" }],
            "aboutus.html": [home, { label: "About Us" }],
            "req1.html": [home, { label: "Requirements" }],
            "requirement.html": [
                home,
                { label: "Requirements", href: `${p}req1.html` },
                { label: "Admission Guide" },
            ],
            "formeq.html": [
                home,
                { label: "Requirements", href: `${p}req1.html` },
                { label: "Application Samples" },
            ],
        };

        return map[file] || [home, { label: document.title || "Page" }];
    }

    function renderBreadcrumb() {
        if (document.querySelector(".site-crumb, .fv-crumb, [data-site-crumb]")) return;
        const trail = breadcrumbTrail();
        if (!trail || !trail.length) return;

        const wrap = document.createElement("div");
        wrap.className = "site-crumb-wrap";
        wrap.setAttribute("data-site-crumb", "true");

        const navCrumb = document.createElement("nav");
        navCrumb.setAttribute("aria-label", "Breadcrumb");

        const ol = document.createElement("ol");
        ol.className = "site-crumb";

        trail.forEach((item, index) => {
            if (index > 0) {
                const sep = document.createElement("li");
                sep.className = "site-crumb-sep";
                sep.setAttribute("aria-hidden", "true");
                sep.textContent = "›";
                ol.appendChild(sep);
            }

            const li = document.createElement("li");
            const isLast = index === trail.length - 1;
            if (isLast || !item.href) {
                const span = document.createElement("span");
                span.textContent = item.label;
                if (isLast) span.setAttribute("aria-current", "page");
                li.appendChild(span);
            } else {
                const a = document.createElement("a");
                a.href = item.href;
                a.textContent = item.label;
                li.appendChild(a);
            }
            ol.appendChild(li);
        });

        navCrumb.appendChild(ol);
        wrap.appendChild(navCrumb);

        const header = document.querySelector("header");
        const primaryNav = document.querySelector("nav.links");
        if (header && header.contains(primaryNav)) {
            header.insertAdjacentElement("afterend", wrap);
        } else if (primaryNav) {
            primaryNav.insertAdjacentElement("afterend", wrap);
        } else {
            document.body.insertAdjacentElement("afterbegin", wrap);
        }
    }

    function renderSearchReturnBar() {
        if (!inUniversities()) return;
        if (document.querySelector(".search-return-bar")) return;

        // Only when arriving from search (?from=search), not from University Lists.
        if (!cameFromSearch()) return;
        const state = loadSearchReturnState();
        if (!state) return;

        const p = pathPrefix();
        const bar = document.createElement("div");
        bar.className = "search-return-bar";
        bar.setAttribute("role", "region");
        bar.setAttribute("aria-label", "Return to search results");

        const inner = document.createElement("div");
        inner.className = "search-return-inner";

        const matchCount = Number(state.matchCount);
        const total = Number(state.total);
        const detailParts = [];
        if (Number.isFinite(matchCount) && matchCount >= 0) {
            detailParts.push(`${matchCount} match${matchCount === 1 ? "" : "es"}`);
        }
        if (Number.isFinite(total) && total > 0) {
            detailParts.push(`${total} total marks`);
        }
        const detailText = detailParts.length ? ` · ${detailParts.join(" · ")}` : "";

        const copy = document.createElement("p");
        copy.innerHTML = `<i class="fas fa-magnifying-glass" aria-hidden="true"></i> Your university matches are still saved${detailText}.`;

        const link = document.createElement("a");
        link.className = "search-return-link";
        link.href = `${p}search.html`;
        link.innerHTML = `<i class="fas fa-arrow-left" aria-hidden="true"></i> Back to search results`;

        inner.append(copy, link);
        bar.appendChild(inner);

        const crumb = document.querySelector(".site-crumb-wrap");
        const primaryNav = document.querySelector("nav.links");
        if (crumb) crumb.insertAdjacentElement("afterend", bar);
        else if (primaryNav) primaryNav.insertAdjacentElement("afterend", bar);
        else document.body.insertAdjacentElement("afterbegin", bar);
    }

    function renderSiteFooter() {
        const p = pathPrefix();
        const markup = `
  <div class="page-shell footer-grid">
    <div class="footer-brand">
      <div class="footer-logo-row">
        <i class="fas fa-graduation-cap" aria-hidden="true"></i>
        <strong>UniFit</strong>
      </div>
      <p>A student-built guide to Myanmar universities, majors, and published admission requirements.</p>
    </div>
    <div>
      <h3>Explore</h3>
      <ul>
        <li><a href="${p}unilists.html">University Lists</a></li>
        <li><a href="${p}search.html">Search Your Uni</a></li>
        <li><a href="${p}req1.html">Requirements</a></li>
        <li><a href="${p}aboutus.html">About Us</a></li>
      </ul>
    </div>
    <div>
      <h3>Project</h3>
      <ul>
        <li>2026 admissions guide support</li>
        <li>Static, privacy-friendly mark matching</li>
        <li>From students, for students</li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <div class="page-shell">
      <p>© UniFit · Own Your Power</p>
    </div>
  </div>`;

        document.querySelectorAll("footer.glass-footer").forEach((node) => node.remove());

        const existing = document.querySelector("footer.site-footer");
        if (existing) {
            existing.className = "site-footer";
            existing.innerHTML = markup;
            return;
        }

        const footer = document.createElement("footer");
        footer.className = "site-footer";
        footer.innerHTML = markup;
        document.body.appendChild(footer);
    }

    function boot() {
        enhanceLogoText();
        enhanceNavIcons();
        enhanceSearchCta();
        setActiveLink();
        renderBreadcrumb();
        renderSearchReturnBar();
        renderSiteFooter();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot, { once: true });
    } else {
        boot();
    }
})();
