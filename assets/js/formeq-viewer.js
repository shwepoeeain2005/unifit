(() => {
  const catalogEl = document.getElementById("docCatalog");
  const viewerRoot = document.querySelector("[data-doc-viewer]");
  if (!catalogEl || !viewerRoot) return;

  const docs = [...catalogEl.querySelectorAll("[data-doc]")].map((group) => {
    const pages = [...group.querySelectorAll("img[data-src], img[src]")].map((img) => ({
      src: img.getAttribute("data-src") || img.getAttribute("src"),
      alt: img.getAttribute("alt") || group.dataset.title || "Document",
      file: (img.getAttribute("data-src") || img.getAttribute("src") || "").split("/").pop(),
    }));
    return {
      id: group.dataset.id,
      title: group.dataset.title || "Document",
      pages,
    };
  }).filter((doc) => doc.pages.length);

  if (!docs.length) return;

  const ui = {
    rail: document.getElementById("docRail"),
    title: document.getElementById("docTitle"),
    sub: document.getElementById("docSub"),
    image: document.getElementById("docImage"),
    stage: document.getElementById("docStage"),
    stageInner: document.getElementById("docStageInner"),
    stageWrap: document.getElementById("docStageWrap"),
    zoomLabel: document.getElementById("zoomLabel"),
    pageLabel: document.getElementById("pageLabel"),
    download: document.getElementById("downloadBtn"),
    lightbox: document.getElementById("docLightbox"),
    lightboxImg: document.getElementById("lightboxImage"),
  };

  let docIndex = 0;
  let pageIndex = 0;
  let zoom = 1;
  const ZOOM_MIN = 0.6;
  const ZOOM_MAX = 3;
  const ZOOM_STEP = 0.2;

  let dragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let scrollLeft = 0;
  let scrollTop = 0;

  function currentDoc() {
    return docs[docIndex];
  }

  function currentPage() {
    return currentDoc().pages[pageIndex];
  }

  function setZoom(next) {
    zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(next * 100) / 100));
    ui.stageInner.style.transform = `scale(${zoom})`;
    ui.zoomLabel.textContent = `${Math.round(zoom * 100)}%`;
  }

  function renderRail() {
    ui.rail.innerHTML = "";
    const heading = document.createElement("p");
    heading.className = "fv-rail-title";
    heading.textContent = "Documents";
    ui.rail.appendChild(heading);

    docs.forEach((doc, dIdx) => {
      const group = document.createElement("div");
      group.className = "fv-group";

      const gTitle = document.createElement("h3");
      gTitle.className = "fv-group-title";
      gTitle.textContent = doc.title;
      group.appendChild(gTitle);

      const thumbs = document.createElement("div");
      thumbs.className = "fv-thumbs";

      doc.pages.forEach((page, pIdx) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "fv-thumb";
        btn.dataset.doc = String(dIdx);
        btn.dataset.page = String(pIdx);
        if (dIdx === docIndex && pIdx === pageIndex) btn.classList.add("is-active");

        btn.innerHTML = `
          <span class="fv-thumb-media"><img src="${page.src}" alt="" loading="lazy" decoding="async"></span>
          <span class="fv-thumb-meta">
            <span class="fv-thumb-label">${doc.pages.length > 1 ? `စာမျက်နှာ ${pIdx + 1}` : "နမူနာ"}</span>
            <span class="fv-thumb-page">${page.file}</span>
          </span>
        `;
        btn.addEventListener("click", () => selectDoc(dIdx, pIdx));
        thumbs.appendChild(btn);
      });

      group.appendChild(thumbs);
      ui.rail.appendChild(group);
    });
  }

  function selectDoc(dIdx, pIdx = 0) {
    docIndex = dIdx;
    pageIndex = Math.max(0, Math.min(pIdx, currentDoc().pages.length - 1));
    setZoom(1);
    renderDoc();
    renderRail();
  }

  function renderDoc() {
    const doc = currentDoc();
    const page = currentPage();
    ui.title.textContent = doc.title;
    ui.sub.textContent = doc.pages.length > 1
      ? `စာမျက်နှာ ${pageIndex + 1} / ${doc.pages.length}`
      : "Application sample document";
    ui.pageLabel.textContent = `Document ${docIndex + 1} of ${docs.length}`;
    ui.image.src = page.src;
    ui.image.alt = page.alt;
    ui.lightboxImg.src = page.src;
    ui.lightboxImg.alt = page.alt;
    ui.download.href = page.src;
    ui.download.setAttribute("download", page.file || "document.webp");
    ui.stage.scrollTop = 0;
    ui.stage.scrollLeft = 0;
  }

  function openLightbox() {
    ui.lightbox.classList.add("is-open");
    ui.lightbox.setAttribute("aria-hidden", "false");
    document.body.classList.add("is-lightbox-open");
  }

  function closeLightbox() {
    ui.lightbox.classList.remove("is-open");
    ui.lightbox.setAttribute("aria-hidden", "true");
    document.body.classList.remove("is-lightbox-open");
  }

  function toggleFullscreen() {
    const active = ui.stageWrap.classList.toggle("is-fullscreen");
    document.body.classList.toggle("is-fs-open", active);
  }

  function exitFullscreen() {
    ui.stageWrap.classList.remove("is-fullscreen");
    document.body.classList.remove("is-fs-open");
  }

  function printDoc() {
    const page = currentPage();
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(`<!DOCTYPE html><html><head><title>${page.file}</title>
      <style>body{margin:0;display:grid;place-items:center;background:#fff}img{max-width:100%;height:auto}</style>
      </head><body><img src="${page.src}" alt="${page.alt}"></body></html>`);
    win.document.close();
    win.focus();
    win.onload = () => {
      win.print();
    };
  }

  document.getElementById("zoomInBtn")?.addEventListener("click", () => setZoom(zoom + ZOOM_STEP));
  document.getElementById("zoomOutBtn")?.addEventListener("click", () => setZoom(zoom - ZOOM_STEP));
  document.getElementById("zoomResetBtn")?.addEventListener("click", () => setZoom(1));
  document.getElementById("fullscreenBtn")?.addEventListener("click", toggleFullscreen);
  document.getElementById("fsExitBtn")?.addEventListener("click", exitFullscreen);
  document.getElementById("printBtn")?.addEventListener("click", printDoc);
  document.getElementById("prevDocBtn")?.addEventListener("click", () => {
    if (pageIndex > 0) selectDoc(docIndex, pageIndex - 1);
    else if (docIndex > 0) selectDoc(docIndex - 1, docs[docIndex - 1].pages.length - 1);
  });
  document.getElementById("nextDocBtn")?.addEventListener("click", () => {
    if (pageIndex < currentDoc().pages.length - 1) selectDoc(docIndex, pageIndex + 1);
    else if (docIndex < docs.length - 1) selectDoc(docIndex + 1, 0);
  });

  ui.image.addEventListener("click", () => {
    if (zoom <= 1.05) openLightbox();
  });
  document.getElementById("lightboxClose")?.addEventListener("click", closeLightbox);
  ui.lightbox?.addEventListener("click", (event) => {
    if (event.target === ui.lightbox) closeLightbox();
  });

  ui.stage.addEventListener("mousedown", (event) => {
    if (zoom <= 1) return;
    dragging = true;
    ui.stage.classList.add("is-dragging");
    dragStartX = event.pageX;
    dragStartY = event.pageY;
    scrollLeft = ui.stage.scrollLeft;
    scrollTop = ui.stage.scrollTop;
  });
  window.addEventListener("mouseup", () => {
    dragging = false;
    ui.stage.classList.remove("is-dragging");
  });
  window.addEventListener("mousemove", (event) => {
    if (!dragging) return;
    ui.stage.scrollLeft = scrollLeft - (event.pageX - dragStartX);
    ui.stage.scrollTop = scrollTop - (event.pageY - dragStartY);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeLightbox();
      exitFullscreen();
    }
    if (event.key === "+" || event.key === "=") setZoom(zoom + ZOOM_STEP);
    if (event.key === "-" || event.key === "_") setZoom(zoom - ZOOM_STEP);
    if (event.key === "0") setZoom(1);
  });

  setZoom(1);
  renderRail();
  renderDoc();
})();
