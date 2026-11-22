(() => {
    const { sections, admissions } = window.unifitDetail ?? { sections: window.unifitSections };
    const placeholders = document.querySelectorAll("template[data-unifit-section]");
    const majors = placeholders[0]?.closest("fieldset");
    if (!Array.isArray(sections) || sections.length !== placeholders.length) {
        throw new Error("UniFit detail data does not match this page.");
    }
    placeholders.forEach((placeholder, index) => {
        const section = sections[index];
        const template = document.createElement("template");
        template.innerHTML = section.html;
        template.content.querySelectorAll("img[src]").forEach((image, position) => {
            const record = section.images[position];
            if (!record) return;
            image.setAttribute("src", record.image_path);
            if (record.alt_text === null) image.removeAttribute("alt");
            else image.setAttribute("alt", record.alt_text);
        });
        placeholder.replaceWith(template.content);
    });

    if (!admissions || !majors) return;

    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = new URL("../css/university-admissions.css?v=2026-admissions-2", document.currentScript.src).href;
    document.head.appendChild(stylesheet);

    function addRules(parent, rules) {
        for (const rule of rules) {
            const line = document.createElement("p");
            line.innerHTML = rule;
            parent.appendChild(line);
        }
    }

    function renderAdmissions() {
        const box = document.createElement("section");
        box.className = "university-admissions";
        box.id = "admission-requirements";
        box.tabIndex = -1;
        const heading = document.createElement("h2");
        heading.textContent = "2026 Admission Requirements";
        box.appendChild(heading);
        if (!admissions.shared.length && !admissions.programmes.length) {
            const note = document.createElement("p");
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
        majors.after(box);
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

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", renderAdmissions, { once: true });
    } else {
        renderAdmissions();
    }
})();
