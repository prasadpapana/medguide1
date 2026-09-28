// ==============================================================================
// MedGuide - Frontend Client Controller
// ==============================================================================

// Session Chat History for AI Chatbot
let chatHistory = [];

// Request In-Flight State Guards (Prevent Duplicate Submissions)
let isSimplifying = false;
let isChatting = false;

// ==============================================================================
// 1. Medical Report Simplifier
// ==============================================================================
async function simplifyReport() {
    if (isSimplifying) return; // Prevent duplicate requests

    const reportInput = document.getElementById("report");
    const resultDiv = document.getElementById("result");
    const simplifyBtn = document.getElementById("simplifyBtn");

    const report = reportInput.value.trim();

    if (report === "") {
        alert("Please enter a medical report or medical term.");
        return;
    }

    isSimplifying = true;
    const originalBtnText = simplifyBtn.innerText;
    simplifyBtn.innerText = "⏳ Simplifying...";
    simplifyBtn.disabled = true;

    try {
        const response = await fetch("/simplify", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                report: report
            })
        });

        const data = await response.json();

        if (data.status === "error") {
            resultDiv.innerHTML = `
                <div class="info-notice" style="border-left-color: #ef4444; color: #b91c1c; background: #fef2f2;">
                    ⚠️ ${escapeHtml(data.result || data.message || "AI explanation service is currently unavailable.")}
                </div>
            `;
            resultDiv.dataset.spokenText = data.result || data.message || "AI explanation service is currently unavailable.";
            return;
        }

        if (data.structured && data.structured.meaning) {
            resultDiv.innerHTML = `
                <div class="explanation-card">
                    <div class="explanation-block">
                        <h4>📖 Meaning</h4>
                        <p>${escapeHtml(data.structured.meaning)}</p>
                    </div>
                    <div class="explanation-block">
                        <h4>💡 In simple words</h4>
                        <p>${escapeHtml(data.structured.in_simple_words)}</p>
                    </div>
                    <div class="explanation-block">
                        <h4>🔍 Example</h4>
                        <p>${escapeHtml(data.structured.example)}</p>
                    </div>
                    <div class="explanation-block note-block">
                        <h4>🛡️ Important note</h4>
                        <p>${escapeHtml(data.structured.important_note)}</p>
                    </div>
                </div>
            `;
            resultDiv.dataset.spokenText = data.result;
        } else {
            resultDiv.innerHTML = `
                <div class="info-notice">
                    ${escapeHtml(data.result || "No explanation available.")}
                </div>
            `;
            resultDiv.dataset.spokenText = data.result;
        }

    } catch (error) {
        resultDiv.innerHTML = `
            <div class="info-notice" style="border-left-color: #ef4444; color: #b91c1c; background: #fef2f2;">
                ⚠️ AI explanation service is currently unavailable. Please check the backend connection or configuration.
            </div>
        `;
        resultDiv.dataset.spokenText = "AI explanation service is currently unavailable. Please check the backend connection or configuration.";
    } finally {
        simplifyBtn.innerText = originalBtnText;
        simplifyBtn.disabled = false;
        isSimplifying = false;
    }
}

// Upload Report File (.txt / .pdf)
async function uploadReportFile() {
    const fileInput = document.getElementById("reportFileInput");
    const fileNameSpan = document.getElementById("reportFileName");
    const reportTextarea = document.getElementById("report");

    if (!fileInput.files || fileInput.files.length === 0) return;

    const file = fileInput.files[0];
    fileNameSpan.innerText = file.name;

    const formData = new FormData();
    formData.append("report_file", file);

    fileNameSpan.innerText = `Reading ${file.name}...`;

    try {
        const response = await fetch("/upload-report", {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        if (data.status === "success" && data.text) {
            reportTextarea.value = data.text;
            fileNameSpan.innerText = `Loaded: ${file.name}`;
        } else if (data.status === "warning") {
            alert(data.message);
            fileNameSpan.innerText = `Scanned PDF detected (${file.name})`;
        } else {
            alert(data.message || "Could not extract text from the uploaded file.");
            fileNameSpan.innerText = file.name;
        }
    } catch (e) {
        alert("Failed to upload and read the report file.");
        fileNameSpan.innerText = file.name;
    }
}

// Copy Explanation to Clipboard
function copyExplanation() {
    const resultDiv = document.getElementById("result");
    const copyBtn = document.getElementById("copyBtn");
    const textToCopy = resultDiv.dataset.spokenText || resultDiv.innerText;

    if (!textToCopy || textToCopy.includes("Your simplified explanation will appear here.")) {
        alert("No explanation available to copy.");
        return;
    }

    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalText = copyBtn.innerText;
        copyBtn.innerText = "✅ Copied!";
        setTimeout(() => {
            copyBtn.innerText = originalText;
        }, 2000);
    }).catch(() => {
        alert("Could not copy text to clipboard.");
    });
}

// Download Explanation as Text File
function downloadExplanation() {
    const resultDiv = document.getElementById("result");
    const textToSave = resultDiv.dataset.spokenText || resultDiv.innerText;

    if (!textToSave || textToSave.includes("Your simplified explanation will appear here.")) {
        alert("No explanation available to download.");
        return;
    }

    const header = "========================================================\n" +
                   "MedGuide - Medical Report Language Explanation\n" +
                   "Educational information only — not a medical diagnosis.\n" +
                   "========================================================\n\n";

    const blob = new Blob([header + textToSave], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "MedGuide_Report_Explanation.txt";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
}

// ==============================================================================
// 2. AI Medical Chatbot
// ==============================================================================
async function sendChatMessage() {
    if (isChatting) return; // Prevent duplicate requests

    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");
    const sendBtn = document.getElementById("chatSendBtn");

    const message = chatInput.value.trim();
    if (!message) return;

    isChatting = true;

    // Add user bubble
    appendChatBubble("user", message);
    chatInput.value = "";
    sendBtn.disabled = true;

    // Add typing placeholder
    const typingBubble = document.createElement("div");
    typingBubble.className = "chat-bubble ai-bubble";
    typingBubble.id = "typingBubble";
    typingBubble.innerHTML = `
        <div class="bubble-header">MedGuide Assistant</div>
        <div class="bubble-body"><em>Thinking...</em></div>
    `;
    chatMessages.appendChild(typingBubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                history: chatHistory
            })
        });

        const data = await response.json();
        if (document.getElementById("typingBubble")) {
            chatMessages.removeChild(typingBubble);
        }

        const aiResponse = data.response || "No response received.";
        appendChatBubble("ai", aiResponse);

        // Update session history (up to last 10 messages)
        chatHistory.push({ role: "user", content: message });
        chatHistory.push({ role: "assistant", content: aiResponse });
        if (chatHistory.length > 10) chatHistory = chatHistory.slice(-10);

    } catch (e) {
        if (document.getElementById("typingBubble")) {
            chatMessages.removeChild(typingBubble);
        }
        appendChatBubble("ai", "⚠️ AI Chat service is currently unavailable. Please try again shortly.");
    } finally {
        sendBtn.disabled = false;
        isChatting = false;
    }
}

function appendChatBubble(sender, text) {
    const chatMessages = document.getElementById("chatMessages");
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender === "user" ? "user-bubble" : "ai-bubble"}`;

    const header = sender === "user" ? "You" : "MedGuide Assistant";
    
    // Convert markdown bold and line breaks for rich reading
    let formattedBody = escapeHtml(text)
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/\n\n/g, "<br><br>")
        .replace(/\n/g, "<br>");

    bubble.innerHTML = `
        <div class="bubble-header">${header}</div>
        <div class="bubble-body">${formattedBody}</div>
    `;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearChat() {
    chatHistory = [];
    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = `
        <div class="chat-bubble ai-bubble">
            <div class="bubble-header">MedGuide Assistant</div>
            <div class="bubble-body">
                Chat cleared. Ask me any medical-language question like <em>"What does anemia mean?"</em>, <em>"What is thrombocytopenia?"</em>, or <em>"What is hemoglobin?"</em>.
            </div>
        </div>
    `;
}

function chatVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const chatVoiceBtn = document.getElementById("chatVoiceBtn");
    const chatInput = document.getElementById("chatInput");

    if (!SpeechRecognition) {
        alert("Voice recognition is not supported in this browser. Please use Chrome or Edge.");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    chatVoiceBtn.innerText = "🔴";
    chatVoiceBtn.disabled = true;

    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript;
        chatInput.value = text;
        sendChatMessage();
    };

    recognition.onend = function() {
        chatVoiceBtn.innerText = "🎤";
        chatVoiceBtn.disabled = false;
    };

    recognition.onerror = function() {
        chatVoiceBtn.innerText = "🎤";
        chatVoiceBtn.disabled = false;
    };

    try {
        recognition.start();
    } catch(e) {
        chatVoiceBtn.innerText = "🎤";
        chatVoiceBtn.disabled = false;
    }
}

// ==============================================================================
// 3. Prescription Image Analyzer
// ==============================================================================
function previewPrescriptionImage() {
    const fileInput = document.getElementById("prescriptionFileInput");
    const fileNameSpan = document.getElementById("prescriptionFileName");
    const previewContainer = document.getElementById("imagePreviewContainer");
    const previewImg = document.getElementById("prescriptionPreview");
    const analyzeBtn = document.getElementById("analyzePrescriptionBtn");
    const resultBox = document.getElementById("prescriptionResult");

    if (!fileInput.files || fileInput.files.length === 0) return;

    const file = fileInput.files[0];
    fileNameSpan.innerText = file.name;

    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.src = e.target.result;
        previewContainer.style.display = "block";
        analyzeBtn.style.display = "inline-flex";
        resultBox.style.display = "none";
    };
    reader.readAsDataURL(file);
}

async function analyzePrescription() {
    const fileInput = document.getElementById("prescriptionFileInput");
    const analyzeBtn = document.getElementById("analyzePrescriptionBtn");
    const resultBox = document.getElementById("prescriptionResult");
    const tableBody = document.getElementById("prescriptionTableBody");
    const clarityNotice = document.getElementById("clarityNotice");
    const medicineExplCards = document.getElementById("medicineExplCards");

    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a prescription image.");
        return;
    }

    const originalBtnText = analyzeBtn.innerText;
    analyzeBtn.innerText = "⏳ Analyzing Prescription...";
    analyzeBtn.disabled = true;

    const formData = new FormData();
    formData.append("prescription_image", fileInput.files[0]);

    try {
        const response = await fetch("/analyze-prescription", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.status === "error") {
            alert(data.message || "Failed to analyze prescription image.");
            return;
        }

        // Render Table
        tableBody.innerHTML = "";
        const medicines = data.medicines || [];

        if (medicines.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align:center; color:#777; padding:16px;">
                        No clearly readable medicines could be extracted. Please check the image clarity or verify with a pharmacist.
                    </td>
                </tr>
            `;
        } else {
            medicines.forEach(m => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${escapeHtml(m.medicine || "Unclear")}</strong></td>
                    <td>${escapeHtml(m.strength || "Unclear")}</td>
                    <td>${escapeHtml(m.frequency || "Unclear")}</td>
                    <td>${escapeHtml(m.timing || "Unclear")}</td>
                    <td>${escapeHtml(m.duration || "Unclear")}</td>
                `;
                tableBody.appendChild(tr);
            });
        }

        // Clarity Note
        if (data.clarity_note) {
            clarityNotice.innerText = `ℹ️ ${data.clarity_note}`;
            clarityNotice.style.display = "block";
        } else {
            clarityNotice.style.display = "none";
        }

        // Explanations
        medicineExplCards.innerHTML = "";
        medicines.forEach(m => {
            if (m.purpose_explanation) {
                const explDiv = document.createElement("div");
                explDiv.className = "med-expl-item";
                explDiv.innerHTML = `
                    <strong>${escapeHtml(m.medicine)}:</strong> ${escapeHtml(m.purpose_explanation)}
                `;
                medicineExplCards.appendChild(explDiv);
            }
        });

        resultBox.style.display = "block";
        resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });

    } catch (e) {
        alert("An error occurred while analyzing the prescription image. Please try again.");
    } finally {
        analyzeBtn.innerText = originalBtnText;
        analyzeBtn.disabled = false;
    }
}

// ==============================================================================
// 4. General Food & Nutrition Information
// ==============================================================================
async function fetchFoodSuggestions() {
    const input = document.getElementById("foodTopicInput");
    const foodBtn = document.getElementById("foodBtn");
    const resultBox = document.getElementById("foodResult");
    const titleEl = document.getElementById("foodResultTitle");
    const bodyEl = document.getElementById("foodResultBody");

    const topic = input.value.trim() || "General balanced wellness";

    const originalText = foodBtn.innerText;
    foodBtn.innerText = "⏳ Loading...";
    foodBtn.disabled = true;

    try {
        const response = await fetch("/food-suggestions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                topic: topic
            })
        });

        const data = await response.json();
        titleEl.innerText = data.title || "General Nutrition Guidance";
        bodyEl.innerText = data.content || "Focus on a balanced variety of vegetables, fruits, whole grains, and water.";
        resultBox.style.display = "block";
        resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });

    } catch (e) {
        titleEl.innerText = "General Nutrition Guidance";
        bodyEl.innerText = "Focus on a balanced variety of whole foods, fresh vegetables, fruits, and proper hydration.";
        resultBox.style.display = "block";
    } finally {
        foodBtn.innerText = originalText;
        foodBtn.disabled = false;
    }
}

function setAndFetchFood(topic) {
    document.getElementById("foodTopicInput").value = topic;
    fetchFoodSuggestions();
}

// ==============================================================================
// 5. Voice Input & Voice Output (Preserved Features)
// ==============================================================================
function speakResult() {
    const resultDiv = document.getElementById("result");
    const speakBtn = document.getElementById("speakBtn");

    const textToSpeak = resultDiv.dataset.spokenText || resultDiv.innerText;

    if (!textToSpeak || textToSpeak.includes("Your simplified explanation will appear here.")) {
        alert("No explanation available to speak.");
        return;
    }

    if (!('speechSynthesis' in window)) {
        alert("Text-to-speech is not supported in this browser.");
        return;
    }

    if (speechSynthesis.speaking) {
        speechSynthesis.cancel();
        speakBtn.innerText = "🔊 Speak Explanation";
        return;
    }

    const voices = speechSynthesis.getVoices();
    const voice = voices.find(v => v.lang.startsWith("en")) || null;

    const speech = new SpeechSynthesisUtterance(textToSpeak);
    if (voice) {
        speech.voice = voice;
        speech.lang = voice.lang;
    } else {
        speech.lang = "en-US";
    }
    speech.rate = 0.95;

    speech.onstart = function () {
        speakBtn.innerText = "⏹️ Stop Speaking";
    };

    speech.onend = function () {
        speakBtn.innerText = "🔊 Speak Explanation";
    };

    speech.onerror = function () {
        speakBtn.innerText = "🔊 Speak Explanation";
    };

    speechSynthesis.cancel();
    speechSynthesis.speak(speech);
}

function startVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const voiceBtn = document.getElementById("voiceBtn");
    const voiceText = document.getElementById("voiceText");
    const reportInput = document.getElementById("report");

    if (!SpeechRecognition) {
        alert("Voice recognition is not supported in this browser. Please use Chrome, Edge, or a compatible browser.");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    voiceBtn.innerText = "🔴 Listening...";
    voiceBtn.disabled = true;
    voiceText.innerText = "Listening... Please speak your medical report clearly.";

    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript;
        voiceText.innerText = "You said: " + text;
        reportInput.value = text;
    };

    recognition.onerror = function(event) {
        voiceText.innerText = "Could not capture voice: " + (event.error || "Please try again.");
    };

    recognition.onend = function() {
        voiceBtn.innerText = "🎤 Start Voice Input";
        voiceBtn.disabled = false;
    };

    try {
        recognition.start();
    } catch (e) {
        voiceBtn.innerText = "🎤 Start Voice Input";
        voiceBtn.disabled = false;
        voiceText.innerText = "Could not start voice recognition. Please try again.";
    }
}

// Utility: Sanitize text to avoid HTML injection
function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}