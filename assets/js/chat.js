(() => {
    const root = new URL("../../", document.currentScript.src);
    const style = document.createElement("link");
    style.rel = "stylesheet";
    style.href = new URL("assets/css/chat.css", root);
    document.head.append(style);

    const widget = document.createElement("aside");
    widget.className = "unifit-chat";
    widget.setAttribute("aria-label", "UniFit Chat");
    widget.innerHTML = `
        <button type="button" class="uc-launcher" aria-label="UniFit Chat" title="UniFit Chat"
                aria-controls="uc-panel" aria-expanded="false">
            <i class="fa-solid fa-comment-dots" aria-hidden="true"></i>
        </button>
        <section id="uc-panel" hidden>
            <header><strong>UniFit Chat</strong>
                <button type="button" class="uc-close" aria-label="Close chat">×</button>
            </header>
            <div class="uc-log" role="log" aria-live="polite" aria-label="Conversation">
                <h2 class="uc-welcome">What would you like to know?</h2>
            </div>
            <div class="uc-starters" role="group" aria-label="Suggested questions">
                <button type="button" data-question="Give me a quick checklist of the documents I need.">Application checklist</button>
                <button type="button" data-question="Compare computing entry requirements at UCSY, UCSM, and NSPU.">Compare universities</button>
                <button type="button" lang="my" data-question="အဝေးသင် သင်တန်းကြေး ဘယ်လောက်လဲ">အဝေးသင် သင်တန်းကြေး</button>
            </div>
            <form><input aria-label="Question" placeholder="Ask in Burmese or English" maxlength="500" required>
                <button type="submit">Send</button>
            </form>
        </section>`;
    document.body.append(widget);

    const toggle = widget.firstElementChild;
    const navActions = document.querySelector("nav.links .nav-actions");
    navActions?.prepend(toggle);
    const panel = widget.querySelector("section");
    const panelHeader = panel.querySelector("header");
    const close = panelHeader.querySelector(".uc-close");
    const narrow = window.matchMedia("(max-width: 1100px)");
    const blocked = new Set();
    const log = widget.querySelector(".uc-log");
    const form = widget.querySelector("form");
    const input = form.querySelector("input");
    const send = form.querySelector("button");
    const welcome = widget.querySelector(".uc-welcome");
    const starters = widget.querySelector(".uc-starters");
    const filePreview = location.protocol === "file:";
    const key = "unifit-chat";
    let state = { messages: [] };
    try {
        const saved = JSON.parse(sessionStorage.getItem(key));
        if (Array.isArray(saved?.messages)) state = saved;
    } catch { /* Storage is optional. */ }

    if (!state.removedOldApplicationExchange) {
        let omit = false;
        state.messages = state.messages.filter((message) => {
            if (message.user) {
                omit = /^what do we need to apply for university[?.!\s]*$/i.test(message.text.trim());
            }
            return !omit;
        });
        if (omit) delete state.previous;
        state.removedOldApplicationExchange = true;
    }
    delete state.open;

    if (filePreview) {
        const notice = document.createElement("p");
        notice.className = "uc-preview-notice";
        notice.textContent = "Open the local UniFit preview to send chat questions.";
        const preview = document.createElement("a");
        const page = location.pathname.slice(root.pathname.length);
        preview.href = new URL(page, "http://127.0.0.1:8091/");
        preview.className = "uc-action";
        preview.textContent = "Open UniFit chat preview";
        notice.append(document.createElement("br"), preview);
        log.append(notice);
        starters.hidden = true;
        form.hidden = true;
    }

    function save() {
        try { sessionStorage.setItem(key, JSON.stringify(state)); }
        catch { /* Keep the current conversation in memory. */ }
    }

    function render(message) {
        welcome.hidden = true;
        const bubble = document.createElement("div");
        bubble.className = message.user ? "uc-question" : "uc-answer";
        bubble.lang = message.language || "";
        bubble.textContent = message.text;
        const pages = message.pages?.length ? message.pages : message.page ? [message.page] : [];
        if (pages.length) {
            const citation = document.createElement("small");
            citation.className = "uc-citation";
            citation.textContent = message.language === "my"
                ? "၂၀၂၆ ဝင်ခွင့်လမ်းညွှန် · စာမျက်နှာ " + pages.map(page => page.toLocaleString("my-MM")).join(", ")
                : "2026 admissions guide · " + pages.join(", ");
            bubble.append(citation);
        }
        const actions = document.createElement("div");
        actions.className = "uc-actions";
        function addLink(path, label, external = false) {
            const url = new URL(path, root);
            if (external ? url.protocol !== "https:" : url.origin !== root.origin) return;
            const link = document.createElement("a");
            link.href = url;
            link.className = external ? "uc-action uc-action--source" : "uc-action";
            link.textContent = label;
            const arrow = document.createElement("span");
            arrow.setAttribute("aria-hidden", "true");
            arrow.textContent = external ? "↗" : "→";
            link.append(arrow);
            actions.append(link);
        }
        if (message.link) {
            const label = message.link.startsWith("universities/") ? "University details" : "Requirements";
            addLink(message.link, message.link_label || (message.link === "search.html" ? "Open Search Your Uni" : label));
        }
        for (const item of message.links || []) addLink(item.url, item.label);
        for (const source of message.sources || []) addLink(source.url, source.label, true);
        log.append(bubble);
        if (actions.childElementCount) log.append(actions);
        log.scrollTop = log.scrollHeight;
    }

    function updateLayout(open) {
        const fullScreen = open && narrow.matches;
        close.hidden = fullScreen;
        document.documentElement.classList.toggle("uc-chat-open", open);
        if (fullScreen) {
            if (toggle.parentElement !== panelHeader) panelHeader.append(toggle);
            for (const sibling of document.body.children) {
                if (sibling !== widget && !sibling.inert) {
                    sibling.inert = true;
                    blocked.add(sibling);
                }
            }
        } else {
            for (const sibling of blocked) sibling.inert = false;
            blocked.clear();
            const home = navActions || widget;
            if (toggle.parentElement !== home) home.prepend(toggle);
        }
        toggle.setAttribute("aria-label", open ? "Close UniFit Chat" : "UniFit Chat");
        toggle.title = open ? "Close UniFit Chat" : "UniFit Chat";
        toggle.firstElementChild.className = open ? "fa-solid fa-xmark" : "fa-solid fa-comment-dots";
    }

    function setOpen(open, focus = false) {
        panel.hidden = !open;
        updateLayout(open);
        toggle.setAttribute("aria-expanded", String(open));
        log.scrollTop = log.scrollHeight;
        if (focus) (open ? (narrow.matches ? toggle : filePreview ? close : input) : toggle).focus();
    }

    if (!filePreview) {
        for (const message of state.messages) render(message);
    }
    save();
    narrow.addEventListener("change", () => {
        if (!panel.hidden) updateLayout(true);
    });
    toggle.addEventListener("click", () => setOpen(panel.hidden, true));
    close.addEventListener("click", () => setOpen(false, true));
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !panel.hidden) setOpen(false, true);
    });
    starters.addEventListener("click", (event) => {
        const question = event.target.closest("button[data-question]")?.dataset.question;
        if (!question || send.disabled) return;
        input.value = question;
        form.requestSubmit();
    });
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (filePreview) return;
        const question = input.value.trim();
        if (!question || send.disabled) return;
        const message = { text: question, user: true };
        const history = state.messages.slice(-6).map(turn => ({ text: turn.text.slice(0, 600), user: !!turn.user }));
        state.messages = [...state.messages, message].slice(-30);
        render(message);
        save();
        input.value = "";
        send.disabled = true;
        try {
            const response = await fetch(new URL("api/chat", root), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question, language: "auto", previous: state.previous, history,
                    page: decodeURIComponent(location.pathname.slice(root.pathname.length)),
                }),
                signal: AbortSignal.timeout(22000),
            });
            if (!response.ok) throw new Error("Chat unavailable");
            const reply = await response.json();
            state.previous = reply.section;
            state.messages = [...state.messages, reply].slice(-30);
            save();
            render(reply);
        } catch {
            render({ text: "UniFit couldn’t get a reply. Please try again." });
        } finally {
            send.disabled = false;
        }
    });
})();
