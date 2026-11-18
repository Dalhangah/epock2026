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
    await mermaid.run({ nodes: [document.getElementById("system-mermaid")] });
    if (!document.querySelector("#system-mermaid svg")) throw new Error("Diagram missing");
    status.textContent = "흐름도 표시 완료. 가로로 밀어 전체를 살펴보세요.";
    const svg = document.querySelector("#system-mermaid svg");
    let diagramWidth = 1600;
    const applySize = () => {
      svg.style.width = `${diagramWidth}px`;
      svg.style.maxWidth = "none";
    };
    applySize();
    document.querySelectorAll("[data-zoom]").forEach((button) => {
      button.addEventListener("click", () => {
        diagramWidth =
          button.dataset.zoom === "reset"
            ? 1600
            : Math.max(
                960,
                Math.min(3200, diagramWidth + (button.dataset.zoom === "in" ? 320 : -320)),
              );
        applySize();
      });
    });
  } catch (error) {
    status.textContent =
      "흐름도를 표시하지 못했습니다. 아래 단계별 설명이나 Mermaid 원본을 확인해 주세요.";
    document.querySelector(".flow-text-detail").open = true;
    console.error("EPOCK diagram rendering failed:", error);
  }
})();
