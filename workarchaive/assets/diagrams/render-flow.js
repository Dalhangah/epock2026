/* Vendored Mermaid; no CDN or external rendering service. */
(async () => {
  const status = document.getElementById("diagram-status");
  try {
    if (!window.mermaid) throw new Error("Mermaid library unavailable");
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "base",
      themeVariables: {
        fontFamily: "Noto Sans CJK KR, Noto Sans, Arial, sans-serif",
        fontSize: "18px",
        primaryTextColor: "#20201e",
        lineColor: "#746b60",
        clusterBkg: "#faf9f6",
        clusterBorder: "#bdb5a9",
      },
      flowchart: {
        htmlLabels: false,
        curve: "basis",
        nodeSpacing: 35,
        rankSpacing: 50,
        padding: 18,
      },
    });
    await mermaid.run({ nodes: document.querySelectorAll(".mermaid") });
    if (!document.querySelector(".mermaid svg")) throw new Error("Diagram missing");
    const svgs = [...document.querySelectorAll(".mermaid svg")];
    let zoom = 1;
    const applySize = () => {
      svgs.forEach((svg) => {
        const viewport = svg.closest(".diagram-scroll");
        const style = getComputedStyle(viewport);
        const paddingX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
        const box = svg.viewBox.baseVal;
        const width = Math.min(viewport.clientWidth - paddingX, (490 * box.width) / box.height);
        svg.style.width = `${Math.max(1, width) * zoom}px`;
        svg.style.maxWidth = "none";
      });
      status.textContent =
        zoom === 1
          ? "단계 순서대로 전체 보기 중입니다. 자세히 보려면 확대하세요."
          : `전체 보기 대비 ${Math.round(zoom * 100)}%. 각 그림 안에서 이동할 수 있습니다.`;
    };
    applySize();
    document.querySelectorAll("[data-zoom]").forEach((button) => {
      button.addEventListener("click", () => {
        zoom =
          button.dataset.zoom === "reset"
            ? 1
            : Math.max(1, Math.min(16, zoom * (button.dataset.zoom === "in" ? 1.5 : 1 / 1.5)));
        applySize();
        if (zoom === 1)
          document.querySelectorAll(".diagram-scroll").forEach((el) => el.scrollTo(0, 0));
      });
    });
    // Refit on mobile rotation/container changes without discarding manual zoom.
    const observer = new ResizeObserver(applySize);
    document.querySelectorAll(".diagram-scroll").forEach((el) => observer.observe(el));
    window.addEventListener("resize", applySize);
  } catch (error) {
    status.textContent =
      "흐름도를 표시하지 못했습니다. 아래 단계별 설명이나 Mermaid 원본을 확인해 주세요.";
    document.querySelector(".flow-text-detail").open = true;
    console.error("EPOCK diagram rendering failed:", error);
  }
})();
