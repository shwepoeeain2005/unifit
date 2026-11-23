(() => {
    const carousel = document.getElementById("logo-carousel");
    const track = document.getElementById("logo-track");
    const featured = document.getElementById("featured-grid");
    const cards = Array.isArray(window.unifitCards) ? window.unifitCards : [];

    function shortName(name) {
        return String(name || "")
            .replace(/\s*-\s*[A-Z0-9()]{2,}$/i, "")
            .replace(/\s*\([^)]*\)\s*$/, "")
            .trim();
    }

    /** Transparent square crest assets (processed from original campus seals). */
    const CREST_CATALOG = [
        { file: "yangon-university-logo.webp", match: (n) => n === "Yangon University" },
        { file: "mandalay-university-logo.webp", match: (n) => n === "Mandalay University" },
        { file: "dagon-university-logo.webp", match: (n) => n === "Dagon University" },
        { file: "east-yangon-university-logo.webp", match: (n) => n === "East Yangon University" },
        { file: "yadabon-university-logo.webp", match: (n) => /yadanabon|yadabon/i.test(n) },
        { file: "mawlamyine-university-logo.webp", match: (n) => n === "Mawlamyine University" },
        { file: "nspu-logo.webp", match: (n) => /nspu/i.test(n) },
        { file: "ytu-removebg-preview.webp", match: (n) => /yangon technological university/i.test(n) },
        { file: "wytu-removebg-preview.webp", match: (n) => /west yangon technological/i.test(n) },
        { file: "uit-removebg-preview.webp", match: (n) => /university of information technology/i.test(n) },
        { file: "um2-removebg-preview.webp", match: (n) => n === "University of Medicine 2" },
        { file: "pu-dawei-logo.webp", match: (n) => /polytechnic university \(dawei\)/i.test(n) },
        { file: "pu-kyaing-tong-logo.webp", match: (n) => /polytechnic university \(kyaing tong\)/i.test(n) },
        { file: "pu-maubin-logo.webp", match: (n) => /polytechnic university \(maubin\)/i.test(n) },
        { file: "pu-panglong-logo.webp", match: (n) => /polytechnic university \(panglong\)/i.test(n) },
        { file: "tu-kalay-logo-removebg-preview.webp", match: (n) => /technological university\(?\s*kalay/i.test(n) },
        { file: "tu-magway-logo-removebg-preview.webp", match: (n) => /technological university\(?\s*magway/i.test(n) },
        { file: "tu-mohywa-logo-removebg-preview.webp", match: (n) => /technological university\(?\s*monywa/i.test(n) },
        { file: "tu-myitkyina-logo-removebg-preview.webp", match: (n) => /polytechnic university \(myitkyina\)/i.test(n) },
        { file: "tu-pakokku-logo-removebg-preview.webp", match: (n) => /technological university\(?\s*pakokku/i.test(n) },
        { file: "tu-sagaing-logo-removebg-preview.webp", match: (n) => /technological university\(?\s*sagaing/i.test(n) },
        { file: "hmawbi-removebg-preview.webp", match: (n) => /technological university \(hmawbi\)/i.test(n) },
        { file: "thanlin-removebg-preview.webp", match: (n) => /technological university \(thanlyin\)/i.test(n) },
        { file: "loikaw-tu-removebg-preview.webp", match: (n) => /polytechnic university \(loikaw\)/i.test(n) },
        { file: "pathein-tu-removebg-preview.webp", match: (n) => /technological university\(?\s*pathein/i.test(n) },
        { file: "pyay-tu-removebg-preview.webp", match: (n) => /pyay technological university/i.test(n) },
        { file: "sittwe-tu-removebg-preview.webp", match: (n) => /technological university\(?\s*sittwe/i.test(n) },
        { file: "taunggyi-tu-removebg-preview.webp", match: (n) => /polytechnic university \(taunggyi\)/i.test(n) },
        { file: "taungoo-tu-removebg-preview.webp", match: (n) => /technological university\(?\s*toungoo/i.test(n) },
        { file: "hinthadacu-logo-removebg-preview.webp", match: (n) => /computer studies \(hinthada\)/i.test(n) },
        { file: "hpa-ancu-logo-removebg-preview.webp", match: (n) => /computer studies \(hpa-?an\)/i.test(n) },
        { file: "patheincu-logo-removebg-preview.webp", match: (n) => /computer studies \(pathein\)/i.test(n) },
        { file: "pyaycu-logo-removebg-preview.webp", match: (n) => /computer studies \(pyay\)/i.test(n) },
        { file: "sittwecu-logo-removebg-preview.webp", match: (n) => /computer studies \(sittwe\)/i.test(n) },
        { file: "thatoncu-logo-removebg-preview.webp", match: (n) => /computer studies \(thaton\)/i.test(n) },
        { file: "p1-1-removebg-preview.webp", match: (n) => /yatanarpon|utycc/i.test(n) },
        { file: "p1-2-removebg-preview.webp" },
        { file: "p1-3-removebg-preview.webp" },
        { file: "p1-4-removebg-preview.webp" },
        { file: "p1-5-removebg-preview.webp" },
        { file: "p1-6-removebg-preview.webp" },
        { file: "p1-8-removebg-preview.webp" },
        { file: "p1-9-removebg-preview.webp" },
        { file: "dentistry-removebg-preview.webp", match: (n) => /dental medicine/i.test(n) },
    ];

    function resolveCrestEntries() {
        return CREST_CATALOG.map((item) => {
            const record = item.match ? cards.find((card) => item.match(card.name || "")) : null;
            return {
                name: record ? record.name : "",
                detail_url: record ? record.detail_url : "",
                logo_path: `assets/images/crests/${item.file}`,
            };
        });
    }

    function buildCrestBadge(entry) {
        const item = document.createElement("div");
        item.className = "campus-crest";
        item.setAttribute("aria-hidden", "true");

        const media = document.createElement("div");
        media.className = "campus-crest-media";
        const img = document.createElement("img");
        img.src = `${entry.logo_path}?v=crest-pad-2`;
        img.alt = "";
        img.loading = "lazy";
        img.decoding = "async";
        img.draggable = false;
        media.appendChild(img);
        item.appendChild(media);
        return item;
    }

    function fillTrack(target, entries) {
        if (!target || !entries.length) return;
        // Two copies enable a seamless -50% CSS loop.
        for (let copy = 0; copy < 2; copy += 1) {
            for (const entry of entries) {
                target.appendChild(buildCrestBadge(entry));
            }
        }
    }

    const crestEntries = resolveCrestEntries();
    if (crestEntries.length) {
        fillTrack(track, crestEntries);

        if (carousel) {
            let resumeTimer = 0;
            const pause = () => {
                carousel.classList.add("is-paused");
                window.clearTimeout(resumeTimer);
            };
            const scheduleResume = () => {
                window.clearTimeout(resumeTimer);
                resumeTimer = window.setTimeout(() => {
                    carousel.classList.remove("is-paused");
                }, 900);
            };

            carousel.addEventListener("mouseenter", pause);
            carousel.addEventListener("mouseleave", () => {
                carousel.classList.remove("is-paused");
            });
            carousel.addEventListener("touchstart", pause, { passive: true });
            carousel.addEventListener("touchend", scheduleResume, { passive: true });
            carousel.addEventListener("touchcancel", scheduleResume, { passive: true });
        }
    }

    if (featured && cards.length) {
        const featuredKeys = [
            "universities/ytu.html",
            "universities/ucsy.html",
            "universities/uit.html",
            "universities/medicine-1.html",
            "universities/yu.html",
            "universities/nspu.html",
        ];
        const categoryLabel = (code) =>
            typeof window.unifitCategoryLabel === "function"
                ? window.unifitCategoryLabel(code)
                : String(code || "").trim() || "University";
        const cleanAddress = (address) =>
            String(address || "")
                .replace(/^📍\s*/u, "")
                .replace(/📍/gu, "")
                .replace(/\s+/g, " ")
                .trim();
        const setupAddressToggle = (card) => {
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
        };
        const byUrl = new Map(cards.map((card) => [card.detail_url, card]));
        for (const url of featuredKeys) {
            const record = byUrl.get(url);
            if (!record) continue;

            const card = document.createElement("article");
            card.className = `card uni-card featured-card is-clickable ${record.categories || ""}`.trim();

            const media = document.createElement("div");
            media.className = "card-media uni-card-media";
            const img = document.createElement("img");
            img.src = record.image_path;
            img.alt = record.name;
            img.loading = "lazy";
            img.decoding = "async";
            const overlay = document.createElement("div");
            overlay.className = "card-overlay uni-card-overlay";
            overlay.setAttribute("aria-hidden", "true");
            const badge = document.createElement("span");
            badge.className = "card-category uni-card-badge";
            badge.textContent = categoryLabel(record.categories);
            media.append(img, overlay, badge);

            const body = document.createElement("div");
            body.className = "card-body uni-card-body";
            const name = document.createElement("h3");
            name.className = "card-title uni-card-title";
            name.textContent = shortName(record.name);

            const location = document.createElement("div");
            location.className = "card-location uni-card-location";
            location.innerHTML =
                '<i class="fas fa-location-dot" aria-hidden="true"></i>';
            const addressBlock = document.createElement("div");
            addressBlock.className = "uni-card-address-block";
            const address = document.createElement("p");
            address.className = "card-address uni-card-address";
            address.textContent = cleanAddress(record.address) || "Myanmar";
            const moreBtn = document.createElement("button");
            moreBtn.type = "button";
            moreBtn.className = "card-address-more uni-card-more";
            moreBtn.hidden = true;
            moreBtn.textContent = "Show more";
            addressBlock.append(address, moreBtn);
            location.appendChild(addressBlock);

            const cta = document.createElement("a");
            cta.className = "card-cta uni-card-cta";
            cta.href = record.detail_url;
            cta.setAttribute("aria-label", `Explore details for ${record.name}`);
            cta.innerHTML =
                '<span>Explore Details</span><i class="fas fa-arrow-up-right" aria-hidden="true"></i>';

            body.append(name, location, cta);
            card.append(media, body);
            card.addEventListener("click", (event) => {
                if (event.target.closest(".card-address-more, .card-cta, a, button")) return;
                window.location.href = record.detail_url;
            });
            featured.appendChild(card);
            setupAddressToggle(card);
        }
    }

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const hero = document.querySelector(".hero");
    const rotateEl = document.getElementById("hero-rotate-text");
    const phrases = [
        "University for you.",
        "Future Campus.",
        "University for your goals.",
        "Journey with UniFit.",
    ];

    if (hero) {
        requestAnimationFrame(() => hero.classList.add("is-ready"));
    }

    if (rotateEl && !prefersReducedMotion) {
        let index = 0;
        window.setInterval(() => {
            rotateEl.classList.remove("is-active");
            rotateEl.classList.add("is-leaving");
            window.setTimeout(() => {
                index = (index + 1) % phrases.length;
                rotateEl.textContent = phrases[index];
                rotateEl.classList.remove("is-leaving");
                rotateEl.classList.add("is-entering");
                // Force reflow so entering state applies before active.
                void rotateEl.offsetWidth;
                rotateEl.classList.remove("is-entering");
                rotateEl.classList.add("is-active");
            }, 450);
        }, 3000);
        rotateEl.classList.add("is-active");
    } else if (rotateEl) {
        rotateEl.classList.add("is-active");
    }

    const statEl = document.querySelector(".stat-count");
    if (statEl) {
        const target = Number(statEl.getAttribute("data-count")) || 150;
        const runCounter = () => {
            if (statEl.dataset.done === "1") return;
            statEl.dataset.done = "1";
            if (prefersReducedMotion) {
                statEl.textContent = String(target);
                return;
            }
            const duration = 1400;
            const start = performance.now();
            const tick = (now) => {
                const progress = Math.min(1, (now - start) / duration);
                const eased = 1 - Math.pow(1 - progress, 3);
                statEl.textContent = String(Math.round(target * eased));
                if (progress < 1) requestAnimationFrame(tick);
                else statEl.textContent = String(target);
            };
            requestAnimationFrame(tick);
        };

        const observeTarget = document.querySelector(".hero-panel") || statEl;
        if ("IntersectionObserver" in window) {
            const observer = new IntersectionObserver(
                (entries) => {
                    for (const entry of entries) {
                        if (!entry.isIntersecting) continue;
                        runCounter();
                        observer.disconnect();
                    }
                },
                { threshold: 0.2, rootMargin: "0px 0px -10% 0px" }
            );
            observer.observe(observeTarget);
            // If already visible on first paint, start after entrance begins.
            window.setTimeout(() => {
                const rect = observeTarget.getBoundingClientRect();
                if (rect.top < window.innerHeight && rect.bottom > 0) runCounter();
            }, 700);
        } else {
            runCounter();
        }
    }

    if (window.ScrollReveal && !prefersReducedMotion) {
        const sr = ScrollReveal({
            distance: "22px",
            duration: 750,
            easing: "ease-out",
            opacity: 0,
            reset: false,
            mobile: true,
            viewFactor: 0.15,
        });

        sr.reveal(".section-heading", {
            delay: 80,
            origin: "bottom",
            distance: "18px",
        });
        sr.reveal(".overview-card", {
            delay: 100,
            interval: 90,
            origin: "bottom",
        });
        sr.reveal(".campus-ribbon", {
            delay: 80,
            origin: "bottom",
            distance: "14px",
            opacity: 0.35,
        });
        sr.reveal(".category-card", {
            delay: 100,
            interval: 100,
            origin: "bottom",
        });
        sr.reveal(".step-card", {
            delay: 100,
            interval: 90,
            origin: "bottom",
        });
        sr.reveal(".featured-card", {
            delay: 120,
            interval: 100,
            origin: "bottom",
        });
        sr.reveal(".final-cta-panel", {
            delay: 100,
            origin: "bottom",
            distance: "18px",
        });
    }
})();
