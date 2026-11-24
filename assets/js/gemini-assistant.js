(() => {
    const panel = document.getElementById("unifit-gemini");
    if (!panel || !window.unifitGemini) {
        return;
    }

    const promptInput = document.getElementById("unifit-gemini-prompt");
    const submitBtn = document.getElementById("unifit-gemini-submit");
    const statusEl = document.getElementById("unifit-gemini-status");
    const answerEl = document.getElementById("unifit-gemini-answer");

    if (!promptInput || !submitBtn || !statusEl || !answerEl) {
        return;
    }

    function setBusy(busy) {
        submitBtn.disabled = busy;
        promptInput.disabled = busy;
        submitBtn.setAttribute("aria-busy", busy ? "true" : "false");
    }

    function setStatus(message, type) {
        statusEl.hidden = !message;
        statusEl.textContent = message || "";
        statusEl.classList.remove("unifit-gemini-status--error", "unifit-gemini-status--loading");
        if (type === "error") {
            statusEl.classList.add("unifit-gemini-status--error");
        } else if (type === "loading") {
            statusEl.classList.add("unifit-gemini-status--loading");
        }
    }

    function showAnswer(text) {
        if (!text) {
            answerEl.hidden = true;
            answerEl.textContent = "";
            return;
        }
        answerEl.hidden = false;
        answerEl.textContent = text;
    }

    async function handleSubmit() {
        if (window.unifitGemini.isLoading()) {
            setStatus("Please wait for the current question to finish.", "error");
            return;
        }

        setBusy(true);
        setStatus("Thinking…", "loading");
        showAnswer("");

        const searchContext = typeof window.unifitSearchSnapshot === "function"
            ? window.unifitSearchSnapshot()
            : null;
        const result = await window.unifitGemini.chat(promptInput.value, searchContext);

        setBusy(false);

        if (!result.ok) {
            setStatus(result.error, "error");
            return;
        }

        setStatus("");
        showAnswer(result.text || "No answer was returned.");
    }

    submitBtn.addEventListener("click", () => {
        void handleSubmit();
    });

    promptInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            void handleSubmit();
        }
    });
})();