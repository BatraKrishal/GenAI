/**
 * Frontend Controller for GBPIET Campus AI Assistant
 * Handles Multi-turn Chat, Voice STT/TTS, Dynamic PDF Ingestion, and Citations.
 */

document.addEventListener("DOMContentLoaded", () => {
    // State variables
    let currentPersona = "Student";
    let currentLang = "en";
    let autoVoiceEnabled = true;
    let isRecording = false;
    let sessionId = "session_" + Math.random().toString(36).substring(2, 9);

    // DOM Elements
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    const micBtn = document.getElementById("micBtn");
    const messagesContainer = document.getElementById("messagesContainer");
    const listeningIndicator = document.getElementById("listeningIndicator");
    const voiceAutoPlayToggle = document.getElementById("voiceAutoPlayToggle");
    const resetChatBtn = document.getElementById("resetChatBtn");
    
    // Ingestion Elements
    const pdfUploadInput = document.getElementById("pdfUploadInput");
    const uploadProgress = document.getElementById("uploadProgress");
    const uploadStatusText = document.getElementById("uploadStatusText");
    const chunkCountEl = document.getElementById("chunkCount");
    const docNameEl = document.getElementById("docName");

    // Modal Elements
    const citationModal = document.getElementById("citationModal");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const modalSource = document.getElementById("modalSource");
    const modalPage = document.getElementById("modalPage");
    const modalSection = document.getElementById("modalSection");
    const modalExcerpt = document.getElementById("modalExcerpt");

    // Initialize System Status
    fetchStatus();

    // -------------------------------------------------------------------------
    // Persona & Language Toggles
    // -------------------------------------------------------------------------
    document.querySelectorAll(".persona-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".persona-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentPersona = btn.getAttribute("data-persona");
        });
    });

    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".lang-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentLang = btn.getAttribute("data-lang");
            if (currentLang === "hi") {
                chatInput.placeholder = "कैम्पस, नियम, फीस या संकाय के बारे में पूछें...";
            } else {
                chatInput.placeholder = "Ask anything about campus, rules, admissions, or faculty...";
            }
        });
    });

    voiceAutoPlayToggle.addEventListener("click", () => {
        autoVoiceEnabled = !autoVoiceEnabled;
        voiceAutoPlayToggle.classList.toggle("active", autoVoiceEnabled);
        voiceAutoPlayToggle.textContent = autoVoiceEnabled ? "🔊 Auto-Voice TTS: ON" : "🔇 Auto-Voice TTS: OFF";
    });

    // -------------------------------------------------------------------------
    // Dynamic PDF Upload (Docling Ingestion)
    // -------------------------------------------------------------------------
    pdfUploadInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        uploadProgress.style.display = "flex";
        uploadStatusText.textContent = `Parsing '${file.name}' with Docling...`;

        try {
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Upload failed");
            }

            const data = await res.json();
            docNameEl.textContent = data.filename;
            chunkCountEl.textContent = `Indexed: ${data.chunks_indexed} chunks (${data.pages_parsed} pgs)`;
            uploadStatusText.textContent = `Ready! (${data.tables_extracted} tables detected)`;
            
            setTimeout(() => {
                uploadProgress.style.display = "none";
            }, 3000);

            appendMessage("assistant", `The document <strong>${data.filename}</strong> has been successfully parsed with IBM Docling! ${data.chunks_indexed} chunks and ${data.tables_extracted} tables are indexed for grounded answers.`);
        } catch (error) {
            uploadStatusText.textContent = "Error: " + error.message;
            setTimeout(() => {
                uploadProgress.style.display = "none";
            }, 4000);
        }
    });

    // -------------------------------------------------------------------------
    // Messaging & Query Handling
    // -------------------------------------------------------------------------
    sendBtn.addEventListener("click", handleSend);
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Quick chips
    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("chip")) {
            chatInput.value = e.target.textContent;
            handleSend();
        }
    });

    async function handleSend() {
        const query = chatInput.value.trim();
        if (!query) return;

        chatInput.value = "";
        appendMessage("user", query);

        // Typing indicator
        const loadingId = appendLoadingMessage();

        try {
            const res = await fetch("/api/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    session_id: sessionId,
                    persona: currentPersona,
                    language: currentLang
                })
            });

            removeLoadingMessage(loadingId);

            if (!res.ok) {
                throw new Error(`Server returned status ${res.status}`);
            }

            const data = await res.json();
            appendAssistantResponse(data);

            // Read aloud if TTS is enabled
            if (autoVoiceEnabled && data.answer) {
                speakText(data.answer, currentLang);
            }
        } catch (err) {
            removeLoadingMessage(loadingId);
            appendMessage("assistant", `Connection error: ${err.message}. Please check if the backend is running.`);
        }
    }

    function appendMessage(role, text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${role}`;
        
        const avatar = role === "user" ? "👤" : "🤖";
        msgDiv.innerHTML = `
            <div class="avatar">${avatar}</div>
            <div class="content"><p>${text}</p></div>
        `;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendAssistantResponse(data) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message assistant";

        let citationsHtml = "";
        if (data.citations && data.citations.length > 0) {
            citationsHtml = `
                <div class="citations-wrapper">
                    <span class="citation-tag-title">Sources:</span>
                    ${data.citations.map((c, i) => `
                        <button class="citation-pill" data-index="${i}">
                            Page ${c.page}
                        </button>
                    `).join("")}
                </div>
            `;
        }

        let followupsHtml = "";
        if (data.suggested_followups && data.suggested_followups.length > 0) {
            followupsHtml = `
                <div class="quick-chips">
                    ${data.suggested_followups.map(f => `<button class="chip">${f}</button>`).join("")}
                </div>
            `;
        }

        // Clean formatted text
        const formattedText = data.answer.replace(/\n/g, "<br>");

        msgDiv.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="content">
                <p>${formattedText}</p>
                ${citationsHtml}
                ${followupsHtml}
                <button class="audio-play-btn" title="Replay Audio">🔊</button>
            </div>
        `;

        // Attach citation click handlers
        if (data.citations) {
            msgDiv.querySelectorAll(".citation-pill").forEach(pill => {
                pill.addEventListener("click", () => {
                    const idx = parseInt(pill.getAttribute("data-index"));
                    showCitationModal(data.citations[idx]);
                });
            });
        }

        // Attach audio replay handler
        const replayBtn = msgDiv.querySelector(".audio-play-btn");
        if (replayBtn) {
            replayBtn.addEventListener("click", () => {
                speakText(data.answer, currentLang);
            });
        }

        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendLoadingMessage() {
        const id = "loading_" + Date.now();
        const msgDiv = document.createElement("div");
        msgDiv.className = "message assistant";
        msgDiv.id = id;
        msgDiv.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="content">
                <p>Verifying with campus dataset...</p>
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return id;
    }

    function removeLoadingMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // -------------------------------------------------------------------------
    // Voice Interaction (STT & TTS) - +10 Bonus Marks
    // -------------------------------------------------------------------------
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        micBtn.addEventListener("click", () => {
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.lang = currentLang === "hi" ? "hi-IN" : "en-US";
                recognition.start();
            }
        });

        recognition.onstart = () => {
            isRecording = true;
            micBtn.classList.add("recording");
            listeningIndicator.style.display = "flex";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            handleSend();
        };

        recognition.onerror = (event) => {
            console.warn("Speech recognition error:", event.error);
        };

        recognition.onend = () => {
            isRecording = false;
            micBtn.classList.remove("recording");
            listeningIndicator.style.display = "none";
        };
    } else {
        micBtn.title = "Speech recognition is not supported in this browser.";
        micBtn.style.opacity = "0.5";
    }

    function speakText(text, lang) {
        if (!window.speechSynthesis) return;

        window.speechSynthesis.cancel(); // Stop current speech
        
        // Strip markdown / html tags for speech
        const cleanText = text.replace(/<[^>]*>/g, "").replace(/\[Doc:[^\]]*\]/g, "");
        const utterance = new SpeechSynthesisUtterance(cleanText);

        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.lang = lang === "hi" ? "hi-IN" : "en-US";

        window.speechSynthesis.speak(utterance);
    }

    // -------------------------------------------------------------------------
    // Citation Modal
    // -------------------------------------------------------------------------
    function showCitationModal(citation) {
        modalSource.textContent = "Source: " + (citation.source || "Official Document");
        modalPage.textContent = "Page: " + (citation.page || "1");
        modalSection.textContent = "Section: " + (citation.section || "General");
        modalExcerpt.textContent = citation.excerpt || "No excerpt available.";
        citationModal.style.display = "flex";
    }

    closeModalBtn.addEventListener("click", () => {
        citationModal.style.display = "none";
    });

    citationModal.addEventListener("click", (e) => {
        if (e.target === citationModal) {
            citationModal.style.display = "none";
        }
    });

    // -------------------------------------------------------------------------
    // System Helpers
    // -------------------------------------------------------------------------
    resetChatBtn.addEventListener("click", async () => {
        await fetch("/api/reset", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `session_id=${sessionId}`
        });
        sessionId = "session_" + Math.random().toString(36).substring(2, 9);
        messagesContainer.innerHTML = `
            <div class="message assistant">
                <div class="avatar">🤖</div>
                <div class="content">
                    <p>Conversation history has been reset. How may I assist you with the campus guidelines?</p>
                </div>
            </div>
        `;
    });

    async function fetchStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();
            chunkCountEl.textContent = `Indexed: ${data.chunks_indexed} chunks`;
        } catch {
            chunkCountEl.textContent = "Status: Connecting...";
        }
    }
});
