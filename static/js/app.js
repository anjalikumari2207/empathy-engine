/* =============================================
   EMPATHY ENGINE — Frontend JS
   ============================================= */

const EMOTION_META = {};

async function loadEmotionMeta() {
  try {
    const res = await fetch("/api/emotions");
    const data = await res.json();
    Object.assign(EMOTION_META, data);
    buildLegend();
  } catch (e) {
    console.warn("Could not load emotion metadata", e);
  }
}

function buildLegend() {
  const voiceMap = {
    excited:   { rate: "1.35–1.5×", pitch: "+8–12st", vol: "95–100%" },
    happy:     { rate: "1.0–1.2×", pitch: "+2–6st",  vol: "85–92%" },
    angry:     { rate: "1.1–1.3×", pitch: "−1–4st",  vol: "92–100%" },
    sad:       { rate: "0.75–0.88×", pitch: "−3–7st", vol: "65–78%" },
    fearful:   { rate: "0.95–1.15×", pitch: "+1–5st", vol: "70–80%" },
    surprised: { rate: "1.05–1.25×", pitch: "+3–9st", vol: "85–95%" },
    concerned: { rate: "0.85–0.95×", pitch: "−1–3st", vol: "78–82%" },
    neutral:   { rate: "1.0×",       pitch: "0st",    vol: "85%" },
  };

  const grid = document.getElementById("legendGrid");
  grid.innerHTML = "";

  for (const [emotion, meta] of Object.entries(EMOTION_META)) {
    const vp = voiceMap[emotion] || {};
    const item = document.createElement("div");
    item.className = "legend-item";
    item.innerHTML = `
      <div class="legend-emoji">${meta.emoji}</div>
      <div>
        <div class="legend-name" style="color:${meta.color}">${emotion}</div>
        <div class="legend-params">
          Rate: ${vp.rate || "—"}<br>
          Pitch: ${vp.pitch || "—"}<br>
          Volume: ${vp.vol || "—"}
        </div>
      </div>`;
    grid.appendChild(item);
  }
}

// ── Textarea counter ──
const textInput = document.getElementById("textInput");
const charCount = document.getElementById("charCount");
textInput.addEventListener("input", () => {
  charCount.textContent = textInput.value.length;
});

// ── Sample pills ──
document.querySelectorAll(".pill").forEach(pill => {
  pill.addEventListener("click", () => {
    textInput.value = pill.dataset.text;
    charCount.textContent = textInput.value.length;
    textInput.focus();
  });
});

// ── Synthesize ──
const btn = document.getElementById("synthesizeBtn");
const btnInner = btn.querySelector(".btn-inner");
const btnLoading = document.getElementById("btnLoading");

btn.addEventListener("click", synthesize);
textInput.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") synthesize();
});

async function synthesize() {
  const text = textInput.value.trim();
  if (!text) { textInput.focus(); return; }

  // Loading state
  btn.disabled = true;
  btnInner.classList.add("hidden");
  btnLoading.classList.add("active");
  hideOutput();

  try {
    const res = await fetch("/api/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });

    const data = await res.json();

    if (!res.ok) {
      showError(data.error || "Request failed");
      return;
    }

    renderOutput(data);

  } catch (err) {
    showError("Network error — is the server running?");
  } finally {
    btn.disabled = false;
    btnInner.classList.remove("hidden");
    btnLoading.classList.remove("active");
  }
}

function hideOutput() {
  document.getElementById("emotionDisplay").style.display = "none";
  document.getElementById("audioSection").style.display = "none";
  document.getElementById("emptyState").style.display = "none";
  document.getElementById("errorState").style.display = "none";
}

function showError(msg) {
  hideOutput();
  document.getElementById("errorMsg").textContent = msg;
  document.getElementById("errorState").style.display = "block";
}

function renderOutput(data) {
  const meta = EMOTION_META[data.emotion] || { emoji: "🎙", color: "#78909C", desc: "" };

  // Emotion badge
  const badge = document.getElementById("emotionBadge");
  badge.style.borderColor = meta.color + "55";
  document.getElementById("emotionEmoji").textContent = meta.emoji;
  document.getElementById("emotionLabel").textContent = data.emotion.toUpperCase();
  document.getElementById("emotionLabel").style.color = meta.color;
  document.getElementById("emotionConf").textContent = `Confidence: ${data.confidence}%`;
  document.getElementById("intensityTag").textContent = data.intensity.toUpperCase();

  // Voice params
  const vp = data.voice_params;
  const rate = vp.rate;
  const pitchSt = parseFloat((vp.pitch || "0").replace("st",""));
  const vol = vp.volume;

  const ratePercent = Math.min(100, Math.max(0, ((rate - 0.7) / (1.6 - 0.7)) * 100));
  const pitchPercent = Math.min(100, Math.max(0, ((pitchSt + 8) / 20) * 100));
  const volPercent = vol;

  document.getElementById("rateBar").style.width = ratePercent + "%";
  document.getElementById("pitchBar").style.width = pitchPercent + "%";
  document.getElementById("volBar").style.width = volPercent + "%";
  document.getElementById("rateVal").textContent = rate.toFixed(2) + "×";
  document.getElementById("pitchVal").textContent = vp.pitch;
  document.getElementById("volVal").textContent = vol + "%";

  // Scores
  const scoreGrid = document.getElementById("scoreGrid");
  scoreGrid.innerHTML = "";
  const sortedScores = Object.entries(data.scores || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  for (const [emo, score] of sortedScores) {
    const m = EMOTION_META[emo] || { emoji: "•" };
    const item = document.createElement("div");
    item.className = "score-item";
    const fillClass = emo === data.emotion ? "score-fill active" : "score-fill";
    item.innerHTML = `
      <span class="score-emoji">${m.emoji}</span>
      <span class="score-name">${emo}</span>
      <div class="score-track"><div class="${fillClass}" style="width:${Math.round(score * 100)}%"></div></div>`;
    scoreGrid.appendChild(item);
  }

  document.getElementById("emotionDisplay").style.display = "block";
  document.getElementById("emotionDisplay").classList.add("fade-in");

  // Audio
  loadAudio(data.audio_url);
}

// ── Audio Player ──
let audioEl = null;
let animFrame = null;

function loadAudio(url) {
  audioEl = document.getElementById("audioPlayer");
  audioEl.src = url;
  audioEl.load();

  const playBtn = document.getElementById("playBtn");
  const progressFill = document.getElementById("progressFill");
  const durationLabel = document.getElementById("durationLabel");
  const progressTrack = document.getElementById("progressTrack");
  const downloadLink = document.getElementById("downloadLink");

  downloadLink.href = url;

  audioEl.onloadedmetadata = () => {
    durationLabel.textContent = formatTime(audioEl.duration);
    drawWaveformPlaceholder();
  };

  audioEl.ontimeupdate = () => {
    if (audioEl.duration) {
      const pct = (audioEl.currentTime / audioEl.duration) * 100;
      progressFill.style.width = pct + "%";
    }
  };

  audioEl.onended = () => {
    playBtn.textContent = "▶";
    progressFill.style.width = "0%";
  };

  playBtn.onclick = () => {
    if (audioEl.paused) {
      audioEl.play();
      playBtn.textContent = "■";
    } else {
      audioEl.pause();
      playBtn.textContent = "▶";
    }
  };

  progressTrack.onclick = (e) => {
    const rect = progressTrack.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    audioEl.currentTime = pct * audioEl.duration;
  };

  document.getElementById("audioSection").style.display = "block";
  document.getElementById("audioSection").classList.add("fade-in");
}

function formatTime(secs) {
  if (!secs || isNaN(secs)) return "0:00";
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

function drawWaveformPlaceholder() {
  const canvas = document.getElementById("waveCanvas");
  const ctx = canvas.getContext("2d");
  canvas.width = canvas.offsetWidth * window.devicePixelRatio || 400;
  canvas.height = 60 * (window.devicePixelRatio || 1);
  ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

  const w = canvas.offsetWidth || 400;
  const h = 60;
  ctx.clearRect(0, 0, w, h);

  const bars = 60;
  const barW = 3;
  const gap = (w - bars * barW) / (bars - 1);

  for (let i = 0; i < bars; i++) {
    const height = 8 + Math.abs(Math.sin(i * 0.35 + Math.random() * 0.2)) * 36;
    const x = i * (barW + gap);
    const y = (h - height) / 2;
    ctx.fillStyle = "rgba(255,107,53,0.35)";
    ctx.beginPath();
    ctx.roundRect(x, y, barW, height, 2);
    ctx.fill();
  }
}

// Init
loadEmotionMeta();
