/**
 * The Empathy Engine — Frontend Logic
 * Handles API calls, UI updates, and audio playback.
 */

(function () {
    "use strict";

    // ---- DOM References ----
    const textInput      = document.getElementById("text-input");
    const charCount      = document.getElementById("char-count");
    const btnSynthesize  = document.getElementById("btn-synthesize");
    const resultsSection = document.getElementById("results-section");
    const errorToast     = document.getElementById("error-toast");
    const errorMessage   = document.getElementById("error-message");

    // Result elements
    const emotionBadge   = document.getElementById("emotion-badge");
    const intensityValue = document.getElementById("intensity-value");
    const intensityFill  = document.getElementById("intensity-fill");
    const scorePos       = document.getElementById("score-pos");
    const scoreNeg       = document.getElementById("score-neg");
    const scoreNeu       = document.getElementById("score-neu");
    const valPos         = document.getElementById("val-pos");
    const valNeg         = document.getElementById("val-neg");
    const valNeu         = document.getElementById("val-neu");
    const descriptionText = document.getElementById("description-text");
    const paramRateVal   = document.getElementById("param-rate-val");
    const paramVolumeVal = document.getElementById("param-volume-val");
    const engineBadge    = document.getElementById("engine-badge");
    const audioPlayer    = document.getElementById("audio-player");
    const downloadLink   = document.getElementById("download-link");

    // ---- State ----
    let isProcessing = false;

    // ---- Character Counter ----
    textInput.addEventListener("input", () => {
        const len = textInput.value.length;
        charCount.textContent = `${len} / 5000`;
    });

    // ---- Example Chips ----
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            textInput.value = chip.dataset.text;
            textInput.dispatchEvent(new Event("input"));
            textInput.focus();
        });
    });

    // ---- Show Error ----
    function showError(msg) {
        errorMessage.textContent = msg;
        errorToast.style.display = "flex";
        setTimeout(() => {
            errorToast.style.display = "none";
        }, 5000);
    }

    // ---- Update Results UI ----
    function updateResults(data) {
        const { emotion, voice_params, audio_url, engine_used } = data;

        // Emotion badge
        if (emotion.secondary_emotion) {
            emotionBadge.textContent = `${emotion.emotion.toUpperCase()} & ${emotion.secondary_emotion.toUpperCase()}`;
        } else {
            emotionBadge.textContent = emotion.emotion.toUpperCase();
        }
        emotionBadge.className = "emotion-badge " + emotion.emotion;

        // Intensity
        const pct = (emotion.intensity * 100).toFixed(1);
        intensityValue.textContent = pct + "%";
        intensityFill.style.width = pct + "%";

        // Sentiment scores
        const scores = emotion.sentiment_scores;
        scorePos.style.width = (scores.pos * 100) + "%";
        scoreNeg.style.width = (scores.neg * 100) + "%";
        scoreNeu.style.width = (scores.neu * 100) + "%";
        valPos.textContent = scores.pos.toFixed(3);
        valNeg.textContent = scores.neg.toFixed(3);
        valNeu.textContent = scores.neu.toFixed(3);

        // Description
        descriptionText.textContent = emotion.description;

        // Voice params
        paramRateVal.textContent   = voice_params.rate_change;
        paramVolumeVal.textContent = voice_params.volume_change;
        engineBadge.textContent    = engine_used;

        // Audio player
        audioPlayer.src = audio_url;
        downloadLink.href = audio_url;

        // Show results
        resultsSection.style.display = "flex";

        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 100);

        // Auto-play
        audioPlayer.play().catch(() => {
            // Autoplay might be blocked by browser policy; that's okay
        });
    }

    // ---- Synthesize ----
    async function synthesize() {
        const text = textInput.value.trim();
        if (!text) {
            showError("Please enter some text first.");
            return;
        }
        if (isProcessing) return;

        isProcessing = true;
        btnSynthesize.classList.add("loading");
        btnSynthesize.disabled = true;

        try {
            const response = await fetch("/api/synthesize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `Server error (${response.status})`);
            }

            const data = await response.json();
            updateResults(data);
        } catch (err) {
            showError(err.message || "Something went wrong. Please try again.");
        } finally {
            isProcessing = false;
            btnSynthesize.classList.remove("loading");
            btnSynthesize.disabled = false;
        }
    }

    btnSynthesize.addEventListener("click", synthesize);

    // Ctrl/Cmd + Enter shortcut
    textInput.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            synthesize();
        }
    });

})();
