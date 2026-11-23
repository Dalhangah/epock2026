/* 공개 시각은 한국시간으로 고정합니다. 기기의 시간대와 무관하게 같은 순간입니다. */
const RELEASE_AT = Date.parse("2026-11-30T16:30:00+09:00");
const RELEASE_DAY = "2026-11-30";

/* 현재 artwork는 MOCK입니다. 실제 작품 검수·게시가 끝나기 전 true로 바꾸지 않습니다. */
const ARTWORK_READY = false;

function getReleaseState(nowMs) {
  const remainingMs = Math.max(0, RELEASE_AT - nowMs);
  const kstDay = new Date(nowMs + 9 * 60 * 60 * 1000).toISOString().slice(0, 10);
  if (remainingMs === 0)
    return {
      phase: ARTWORK_READY ? "open" : "pending",
      label: ARTWORK_READY ? "NOW OPEN" : "공개 준비 중",
    };
  if (kstDay < RELEASE_DAY) {
    const days = Math.round(
      (Date.parse(RELEASE_DAY + "T00:00:00Z") - Date.parse(kstDay + "T00:00:00Z")) / 86400000,
    );
    return { phase: "days", label: `D−${days}` };
  }
  const totalSeconds = Math.ceil(remainingMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return {
    phase: "countdown",
    label: [hours, minutes, seconds].map((n) => String(n).padStart(2, "0")).join(" : "),
  };
}

if (typeof document !== "undefined") {
  let lastPhase;
  function updateCountdown() {
    const state = getReleaseState(Date.now());
    document.getElementById("countdown").textContent = state.label;
    document.getElementById("countdown-caption").textContent =
      state.phase === "countdown"
        ? "시 · 분 · 초 / 한국시간 기준"
        : state.phase === "days"
          ? "함께 만날 날을 기다립니다."
          : "EPOCK2026";
    document.getElementById("artwork-link").hidden = state.phase !== "open";
    document.querySelectorAll("[data-coming-soon]").forEach((element) => {
      element.hidden = state.phase === "pending" || state.phase === "open";
    });
    if (state.phase !== lastPhase) {
      document.getElementById("release-status").textContent =
        state.phase === "pending"
          ? "예정된 공개 시각이 지났습니다. 작품 공개 준비가 끝나는 대로 안내하겠습니다."
          : state.phase === "open"
            ? "작품이 공개되었습니다. 아래 버튼을 눌러 감상해 주세요."
            : "";
      lastPhase = state.phase;
    }
  }
  updateCountdown();
  setInterval(updateCountdown, 1000);
  document.addEventListener("visibilitychange", updateCountdown);
}
if (typeof module !== "undefined") module.exports = { getReleaseState, RELEASE_AT };
