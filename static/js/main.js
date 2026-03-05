// ====================================================
// main.js - Pray ON 클라이언트 JavaScript
// ====================================================
// 이 파일은 브라우저에서 실행되는 코드입니다.
// Flask 서버의 API를 호출하고, 결과를 화면에 표시합니다.
// ====================================================

// ── 페이지 로드 완료 시 실행 ──
document.addEventListener("DOMContentLoaded", () => {
    setupCharCounter();   // 글자 수 카운터 초기화
});


// ──────────────────────────────────────────────
// 전역 변수 및 초기화
// ──────────────────────────────────────────────

let currentPrayerText = ""; // 현재 화면에 표시된 기도문 저장 (목소리 변경 시 사용)
let currentEmotion = "";    // 현재 기도 제목(감정) 저장 (파일명 생성용)


// ──────────────────────────────────────────────
// 글자 수 카운터
// ──────────────────────────────────────────────

/**
 * 텍스트에어리어의 글자 수를 실시간으로 표시합니다.
 */
function setupCharCounter() {
    const textarea = document.getElementById("emotion-input");
    const counter = document.getElementById("char-count");

    if (!textarea || !counter) return;

    textarea.addEventListener("input", () => {
        counter.textContent = textarea.value.length;
        // 450자 이상이면 빨간색으로 경고
        counter.style.color = textarea.value.length >= 450 ? "#e74c3c" : "";
    });

    // Enter 키(Shift+Enter = 줄바꿈, Enter 단독 = 생성 실행)
    textarea.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();       // 기본 줄바꿈 방지
            generatePrayer();          // 기도문 생성 실행
        }
    });
}


// ──────────────────────────────────────────────
// 기도문 생성 (핵심 기능)
// ──────────────────────────────────────────────

/**
 * 사용자가 "기도문 만들기" 버튼을 클릭하면 실행됩니다.
 * Flask 서버의 /generate API를 호출해서 기도문과 음성 파일을 받아옵니다.
 */
async function generatePrayer() {
    const textarea = document.getElementById("emotion-input");
    const generateBtn = document.getElementById("generate-btn");
    const emotion = textarea.value.trim();

    // ⚙️ 설정에서 '목소리(voice)' 선택값을 가져옵니다. (말투 톤 설정은 제거됨)
    const voiceSelect = document.getElementById("voice-select");
    const voice = voiceSelect ? voiceSelect.value : "21m00Tcm4TlvDq8ikWAM";

    // 입력이 비어 있으면 실행하지 않습니다.
    if (!emotion) {
        textarea.focus();
        textarea.style.borderColor = "#e74c3c";
        setTimeout(() => (textarea.style.borderColor = ""), 1500);
        return;
    }

    // ① 로딩 상태 시작
    setLoadingState(true, generateBtn);

    try {
        // ② Flask 서버의 /generate API에 POST 요청을 보냅니다.
        // fetch는 브라우저 내장 함수로, 서버와 데이터를 주고받습니다.
        const response = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" }, // JSON 형식으로 보냄
            body: JSON.stringify({
                emotion: emotion,
                voice: voice
            }),        // 사용자 입력과 설정값을 JSON으로 변환
        });

        // ③ 서버 응답을 JSON으로 파싱합니다.
        const data = await response.json();

        if (data.success) {
            currentEmotion = emotion; // 성공 시 제목 저장
            // ④ 성공 시 기도문과 오디오 플레이어를 화면에 표시
            displayPrayer(data.prayer, data.audio_url);
        } else {
            // ⑤ 서버에서 오류 메시지를 보낸 경우
            showError(data.error || "기도문 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.");
        }

    } catch (error) {
        // ⑥ 네트워크 오류 등 예외 처리
        console.error("API 호출 오류:", error);
        showError("서버와 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요.");

    } finally {
        // ⑦ 성공/실패에 관계없이 로딩 상태 종료
        setLoadingState(false, generateBtn);
    }
}


/**
 * 로딩 상태를 켜고 끄는 함수.
 * @param {boolean} isLoading - true면 로딩 시작, false면 종료
 * @param {HTMLElement} btn - 비활성화할 버튼 요소
 */
function setLoadingState(isLoading, btn) {
    const loadingSection = document.getElementById("loading-section");
    const outputSection = document.getElementById("prayer-output-section");

    if (isLoading) {
        // 로딩 시작: 로딩 표시를 보이고, 결과 영역과 버튼을 숨깁니다.
        loadingSection.classList.remove("hidden");
        outputSection.classList.add("hidden");
        btn.disabled = true;
        btn.querySelector(".btn-text").textContent = "기도문 생성 중…";
    } else {
        // 로딩 종료: 로딩 표시를 숨기고 버튼을 다시 활성화합니다.
        loadingSection.classList.add("hidden");
        btn.disabled = false;
        btn.querySelector(".btn-text").textContent = "기도문 만들기";
    }
}


/**
 * 생성된 기도문과 오디오 플레이어를 화면에 표시합니다.
 * @param {string} prayerText - 기도문 텍스트
 * @param {string} audioUrl   - 음성 파일 URL
 */
function displayPrayer(prayerText, audioUrl) {
    currentPrayerText = prayerText; // 현재 기도문 저장
    const outputSection = document.getElementById("prayer-output-section");
    const prayerTextEl = document.getElementById("prayer-text");
    const audioEl = document.getElementById("prayer-audio");
    const audioSection = document.getElementById("audio-player-section");

    // 기도문 텍스트 표시 (성경 구절은 금색으로 강조)
    prayerTextEl.innerHTML = highlightBibleRefs(prayerText);

    // 오디오 플레이어 설정
    if (audioUrl) {
        audioEl.src = audioUrl;
        audioSection.classList.remove("hidden");
        // 자동으로 재생을 시작합니다 (브라우저 정책에 따라 자동재생이 막힐 수 있음)
        audioEl.load();
        // 약간의 딜레이 후 자동 재생 시도
        setTimeout(() => audioEl.play().catch(() => { }), 500);
    } else {
        audioSection.classList.add("hidden");
    }

    // 결과 카드를 보이게 합니다.
    outputSection.classList.remove("hidden");

    // 결과 영역으로 부드럽게 스크롤합니다.
    outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
}


/**
 * 기도문 텍스트에서 성경 구절 참조를 찾아 금색으로 강조 표시합니다.
 * 예: (시편 23:4) → <span class="bible-ref">(시편 23:4)</span>
 * @param {string} text - 원본 기도문 텍스트
 * @returns {string} HTML이 포함된 텍스트
 */
function highlightBibleRefs(text) {
    // XSS 방지: 먼저 HTML 특수문자를 이스케이프합니다.
    const escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // 줄바꿈 문자를 <br> 태그로 변환합니다.
    const withLineBreaks = escaped.replace(/\n/g, "<br>");

    // 성경 구절 패턴을 찾아 강조 표시합니다.
    // 패턴: (책이름 숫자:숫자) 형태
    return withLineBreaks.replace(
        /\(([^)]*\d+:\d+[^)]*)\)/g,
        '<span class="bible-ref">($1)</span>'
    );
}


// ──────────────────────────────────────────────
// 유틸리티 기능
// ──────────────────────────────────────────────

/**
 * 기도문 텍스트를 클립보드에 복사합니다.
 */
function copyPrayer() {
    const prayerText = document.getElementById("prayer-text").innerText;
    navigator.clipboard.writeText(prayerText).then(() => {
        showToast("📋 기도문이 클립보드에 복사되었습니다!");
    }).catch(() => {
        // 구형 브라우저 대비 fallback
        const tempEl = document.createElement("textarea");
        tempEl.value = prayerText;
        document.body.appendChild(tempEl);
        tempEl.select();
        document.execCommand("copy");
        document.body.removeChild(tempEl);
        showToast("📋 기도문이 복사되었습니다!");
    });
}


/**
 * 새 기도문을 작성하기 위해 화면을 초기 상태로 되돌립니다.
 */
function newPrayer() {
    document.getElementById("prayer-output-section").classList.add("hidden");
    const textarea = document.getElementById("emotion-input");
    textarea.value = "";
    document.getElementById("char-count").textContent = "0";
    textarea.focus();

    // 입력 섹션으로 스크롤
    document.getElementById("input-section").scrollIntoView({ behavior: "smooth" });
}


/**
 * 오류 메시지를 사용자에게 보여주는 함수.
 * @param {string} message - 표시할 오류 메시지
 */
function showError(message) {
    showToast("⚠️ " + message, 4000);
}


/**
 * 화면 하단에 잠깐 나타났다가 사라지는 알림(토스트)을 표시합니다.
 * @param {string} message - 표시할 메시지
 * @param {number} duration - 표시 시간 (밀리초, 기본 2500ms)
 */
function showToast(message, duration = 2500) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.remove("hidden");

    // 한 프레임 기다린 후 'show' 클래스를 추가해서 애니메이션 실행
    requestAnimationFrame(() => {
        toast.classList.add("show");
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.classList.add("hidden"), 400);
        }, duration);
    });
}


// ──────────────────────────────────────────────
// 기도 기록 (History)
// ──────────────────────────────────────────────

let historyLoaded = false; // 기록을 이미 불러왔는지 여부

/**
 * 기도 기록 섹션을 열고 닫습니다.
 * 처음 열 때 서버에서 기록을 불러옵니다.
 */
async function toggleHistory() {
    const content = document.getElementById("history-content");
    const arrow = document.getElementById("toggle-arrow");
    const toggleEl = document.getElementById("history-toggle");
    const isExpanded = !content.classList.contains("hidden");

    if (isExpanded) {
        // 닫기
        content.classList.add("hidden");
        arrow.classList.remove("open");
        toggleEl.setAttribute("aria-expanded", "false");
    } else {
        // 열기
        content.classList.remove("hidden");
        arrow.classList.add("open");
        toggleEl.setAttribute("aria-expanded", "true");

        // 처음 열 때만 서버에서 기록을 가져옵니다.
        if (!historyLoaded) {
            await loadHistory();
            historyLoaded = true;
        }
    }
}


/**
 * 서버(/history)에서 기도 기록을 가져와서 목록으로 렌더링합니다.
 */
async function loadHistory() {
    const listEl = document.getElementById("history-list");
    listEl.innerHTML = '<p class="empty-state">기록을 불러오는 중입니다…</p>';

    try {
        const response = await fetch("/history");
        const data = await response.json();

        if (!data.success) throw new Error(data.error);

        if (data.prayers.length === 0) {
            listEl.innerHTML = '<p class="empty-state">저장된 기도 기록이 없습니다.<br/>첫 번째 기도문을 만들어보세요! 🙏</p>';
            return;
        }

        // 기도 기록 목록을 HTML로 렌더링합니다.
        listEl.innerHTML = data.prayers.map(p => createHistoryItemHTML(p)).join("");

    } catch (error) {
        console.error("기도 기록 조회 오류:", error);
        listEl.innerHTML = '<p class="empty-state">⚠️ 기록을 불러오지 못했습니다. Firebase 설정을 확인해 주세요.</p>';
    }
}


/**
 * 개별 기도 기록 카드의 HTML을 생성합니다.
 * @param {object} prayer - 기도 기록 객체
 * @returns {string} HTML 문자열
 */
function createHistoryItemHTML(prayer) {
    // XSS 방지를 위해 사용자 입력 데이터를 이스케이프합니다.
    const safeEmotion = escapeHTML(prayer.emotion);
    const safeDate = escapeHTML(prayer.created_at);
    const safePrayer = highlightBibleRefs(prayer.prayer || "");
    const audioHTML = prayer.audio_url
        ? `<audio class="history-audio" controls src="${escapeHTML(prayer.audio_url)}"></audio>`
        : "";

    return `
    <div class="history-item" id="item-${prayer.id}">
      <div class="history-item-header" onclick="toggleHistoryItem('${prayer.id}')">
        <span class="history-emotion">${safeEmotion}</span>
        <span class="history-date">${safeDate}</span>
      </div>
      <div class="history-item-body hidden" id="body-${prayer.id}">
        ${audioHTML}
        <p class="history-prayer-text">${safePrayer}</p>
        <div class="history-actions">
          <button class="btn--danger" onclick="deletePrayer('${prayer.id}')">🗑 삭제</button>
        </div>
      </div>
    </div>
  `;
}


/**
 * 개별 기도 기록 항목을 펼치거나 접습니다.
 * @param {string} id - 기도 기록 문서 ID
 */
function toggleHistoryItem(id) {
    const body = document.getElementById(`body-${id}`);
    if (body) body.classList.toggle("hidden");
}


/**
 * 기도 기록을 서버에서 삭제합니다.
 * @param {string} docId - 삭제할 Firestore 문서 ID
 */
async function deletePrayer(docId) {
    if (!confirm("이 기도 기록을 삭제할까요?")) return;

    try {
        const response = await fetch(`/history/${docId}`, { method: "DELETE" });
        const data = await response.json();

        if (data.success) {
            // 화면에서도 해당 항목을 제거합니다.
            const item = document.getElementById(`item-${docId}`);
            if (item) {
                item.style.opacity = "0";
                item.style.transform = "translateX(20px)";
                item.style.transition = "all 0.3s ease";
                setTimeout(() => item.remove(), 300);
            }
            showToast("🗑 기도 기록이 삭제되었습니다.");
        } else {
            showError(data.error || "삭제에 실패했습니다.");
        }
    } catch (error) {
        console.error("삭제 오류:", error);
        showError("삭제 중 오류가 발생했습니다.");
    }
}


// ──────────────────────────────────────────────
// 보안 유틸리티
// ──────────────────────────────────────────────

/**
 * XSS(크로스 사이트 스크립팅) 공격 방지를 위해
 * HTML 특수문자를 안전한 문자로 변환합니다.
 * @param {string} str - 변환할 문자열
 * @returns {string} 이스케이프된 문자열
 */
function escapeHTML(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
/**
 * 목소리 선택 변경 시 즉시 새로운 목소리로 재생합니다.
 */
document.getElementById("voice-select")?.addEventListener("change", async function () {
    if (!currentPrayerText) return; // 생성된 기도문이 없으면 무시

    const voice = this.value;
    const audioEl = document.getElementById("prayer-audio");

    // 로딩 표시 (옵션: 간단하게 버튼 텍스트 변경 등)
    console.log("🎙️ 목소리 변경 시도 중:", voice);

    try {
        const response = await fetch("/tts-only", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prayer: currentPrayerText,
                voice: voice,
                title: currentEmotion || "기도문"
            })
        });

        const data = await response.json();
        if (data.success && data.audio_url) {
            audioEl.src = data.audio_url;
            audioEl.load();
            audioEl.play().catch(e => console.warn("자동 재생 차단됨:", e));
            showToast("🔊 선택하신 목소리로 재생을 시작합니다.");
        }
    } catch (error) {
        console.error("목소리 변경 중 TTS 호출 오류:", error);
    }
});
