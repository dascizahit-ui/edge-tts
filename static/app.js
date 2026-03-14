// ==========================================
//  SesForge — Client Logic
// ==========================================

const $ = (sel) => document.querySelector(sel);
const textInput = $("#textInput");
const charCount = $("#charCount");
const clearBtn = $("#clearBtn");
const langSelect = $("#languageSelect");
const voiceSelect = $("#voiceSelect");
const rateSlider = $("#rateSlider");
const pitchSlider = $("#pitchSlider");
const volumeSlider = $("#volumeSlider");
const rateValue = $("#rateValue");
const pitchValue = $("#pitchValue");
const volumeValue = $("#volumeValue");
const synthBtn = $("#synthBtn");
const playerSection = $("#playerSection");
const playBtn = $("#playBtn");
const downloadBtn = $("#downloadBtn");
const progressTrack = $("#progressTrack");
const progressFill = $("#progressFill");
const progressThumb = $("#progressThumb");
const currentTimeEl = $("#currentTime");
const durationEl = $("#duration");
const waveform = $("#waveform");
const audioPlayer = $("#audioPlayer");

let currentFilename = null;

// ---- Voice population ----
function populateVoices() {
  const lang = langSelect.value;
  const voices = VOICES[lang] || [];
  voiceSelect.innerHTML = "";
  voices.forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v.name;
    opt.textContent = v.label;
    voiceSelect.appendChild(opt);
  });
}

langSelect.addEventListener("change", populateVoices);
populateVoices();

// ---- Char counter ----
textInput.addEventListener("input", () => {
  const len = textInput.value.length;
  charCount.textContent = len;
  if (len > 4500) {
    charCount.classList.add("warn");
  } else {
    charCount.classList.remove("warn");
  }
});

// ---- Clear button ----
clearBtn.addEventListener("click", () => {
  textInput.value = "";
  charCount.textContent = "0";
  charCount.classList.remove("warn");
  textInput.focus();
});

// ---- Slider labels ----
function updateSliderLabel(slider, label, suffix) {
  const val = parseInt(slider.value);
  label.textContent = (val >= 0 ? "+" : "") + val + suffix;
}

rateSlider.addEventListener("input", () =>
  updateSliderLabel(rateSlider, rateValue, "%"),
);
pitchSlider.addEventListener("input", () =>
  updateSliderLabel(pitchSlider, pitchValue, "Hz"),
);
volumeSlider.addEventListener("input", () =>
  updateSliderLabel(volumeSlider, volumeValue, "%"),
);

// ---- Waveform bars ----
function generateWaveformBars() {
  waveform.innerHTML = "";
  const count = Math.floor(waveform.offsetWidth / 5) || 80;
  for (let i = 0; i < count; i++) {
    const bar = document.createElement("div");
    bar.className = "bar";
    const h = Math.random() * 40 + 8;
    bar.style.height = h + "px";
    waveform.appendChild(bar);
  }
}

// ---- Toast ----
function showToast(msg, isError = true) {
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.background = isError ? "var(--danger)" : "var(--success)";
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3500);
}

// ---- Synthesize ----
synthBtn.addEventListener("click", async () => {
  const text = textInput.value.trim();
  if (!text) {
    showToast("Lütfen bir metin girin.");
    textInput.focus();
    return;
  }

  synthBtn.disabled = true;
  synthBtn.classList.add("loading");

  const rateVal = parseInt(rateSlider.value);
  const pitchVal = parseInt(pitchSlider.value);
  const volVal = parseInt(volumeSlider.value);

  const body = {
    text: text,
    voice: voiceSelect.value,
    rate: (rateVal >= 0 ? "+" : "") + rateVal + "%",
    pitch: (pitchVal >= 0 ? "+" : "") + pitchVal + "Hz",
    volume: (volVal >= 0 ? "+" : "") + volVal + "%",
  };

  try {
    const res = await fetch("/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    // Response'un content-type'ını kontrol et
    const contentType = res.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      throw new Error(
        "Server yanıtı JSON formatında değil. Repl uyuyor olabilir.",
      );
    }

    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || "Bir hata oluştu.");
      return;
    }

    currentFilename = data.filename;
    audioPlayer.src = `/audio/${currentFilename}`;
    audioPlayer.load();

    playerSection.classList.remove("visible");
    void playerSection.offsetWidth; // force reflow
    playerSection.classList.add("visible");
    generateWaveformBars();

    showToast("Ses başarıyla oluşturuldu!", false);
  } catch (err) {
    console.error("Fetch error:", err);
    showToast("Bağlantı hatası: " + err.message);
  } finally {
    synthBtn.disabled = false;
    synthBtn.classList.remove("loading");
  }
});

// ---- Audio Player ----
let isPlaying = false;

playBtn.addEventListener("click", () => {
  if (!audioPlayer.src) return;
  if (isPlaying) {
    audioPlayer.pause();
  } else {
    audioPlayer.play();
  }
});

audioPlayer.addEventListener("play", () => {
  isPlaying = true;
  $(".icon-play").style.display = "none";
  $(".icon-pause").style.display = "block";
});

audioPlayer.addEventListener("pause", () => {
  isPlaying = false;
  $(".icon-play").style.display = "block";
  $(".icon-pause").style.display = "none";
});

audioPlayer.addEventListener("ended", () => {
  isPlaying = false;
  $(".icon-play").style.display = "block";
  $(".icon-pause").style.display = "none";
  progressFill.style.width = "0%";
  progressThumb.style.left = "0%";
});

audioPlayer.addEventListener("timeupdate", () => {
  if (!audioPlayer.duration) return;
  const pct = (audioPlayer.currentTime / audioPlayer.duration) * 100;
  progressFill.style.width = pct + "%";
  progressThumb.style.left = pct + "%";
  currentTimeEl.textContent = formatTime(audioPlayer.currentTime);

  // Animate waveform bars
  const bars = waveform.querySelectorAll(".bar");
  const activePct = pct / 100;
  bars.forEach((bar, i) => {
    if (i / bars.length <= activePct) {
      bar.classList.add("active");
    } else {
      bar.classList.remove("active");
    }
  });
});

audioPlayer.addEventListener("loadedmetadata", () => {
  durationEl.textContent = formatTime(audioPlayer.duration);
});

// Progress seek
progressTrack.addEventListener("click", (e) => {
  if (!audioPlayer.duration) return;
  const rect = progressTrack.getBoundingClientRect();
  const pct = (e.clientX - rect.left) / rect.width;
  audioPlayer.currentTime = pct * audioPlayer.duration;
});

// Download
downloadBtn.addEventListener("click", () => {
  if (!currentFilename) return;
  const a = document.createElement("a");
  a.href = `/download/${currentFilename}`;
  a.download = "";
  document.body.appendChild(a);
  a.click();
  a.remove();
});

// ---- Helpers ----
function formatTime(sec) {
  if (isNaN(sec)) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return m + ":" + (s < 10 ? "0" : "") + s;
}

// ---- Keyboard shortcut ----
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") {
    synthBtn.click();
  }
});
