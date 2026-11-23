/* Shared UniFit category labels — used by list, search, and homepage */
(() => {
    const LABELS = {
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

    window.unifitCategoryLabel = function unifitCategoryLabel(code) {
        const key = String(code || "").trim();
        return LABELS[key] || key || "University";
    };

    window.unifitCategoryLabels = LABELS;
})();
