/**
 * script.js — Summarify Frontend Logic
 * Handles user interactions, API calls, and dynamic UI updates.
 */

// ═══════════════════════════════════════════════════════════════════
//  Configuration
// ═══════════════════════════════════════════════════════════════════

const API_BASE = "http://localhost:5000/api";

// ═══════════════════════════════════════════════════════════════════
//  DOM Elements
// ═══════════════════════════════════════════════════════════════════

const elements = {
    // Tabs
    tabBtns:          document.querySelectorAll(".tab[data-tab]"),
    tabContents:      document.querySelectorAll(".tab-content"),

    // Text Input
    textInput:        document.getElementById("text-input"),
    wordCountDisplay: document.getElementById("word-count-display"),

    // File Upload
    dropZone:         document.getElementById("drop-zone"),
    fileInput:        document.getElementById("file-input"),
    fileInfo:         document.getElementById("file-info"),
    fileName:         document.getElementById("file-name"),
    removeFileBtn:    document.getElementById("remove-file-btn"),

    // Settings
    formatOptions:    document.querySelectorAll('#format-options .radio-card'),
    lengthOptions:    document.querySelectorAll('#length-options .radio-card'),
    methodOptions:    document.querySelectorAll('#method-options .radio-card'),

    // Actions
    summarizeBtn:     document.getElementById("summarize-btn"),

    // Output
    outputSection:    document.getElementById("output-section"),
    summaryOutput:    document.getElementById("summary-output"),
    outputMethod:     document.getElementById("output-method"),
    outputStats:      document.getElementById("output-stats"),
    copyBtn:          document.getElementById("copy-btn"),
    downloadTxtBtn:   document.getElementById("download-txt-btn"),
    downloadPdfBtn:   document.getElementById("download-pdf-btn"),

    // Loading
    loadingOverlay:   document.getElementById("loading-overlay"),

    // History
    historyList:      document.getElementById("history-list"),
    clearHistoryBtn:  document.getElementById("clear-history-btn"),

    // Dark mode
    darkModeToggle:   document.getElementById("dark-mode-toggle"),
    iconSun:          document.getElementById("icon-sun"),
    iconMoon:         document.getElementById("icon-moon"),

    // Toast
    toast:            document.getElementById("toast"),
};

// ═══════════════════════════════════════════════════════════════════
//  State
// ═══════════════════════════════════════════════════════════════════

let state = {
    activeTab:    "text-tab",   // "text-tab" | "upload-tab"
    selectedFile: null,
    summaryType:  "paragraph",  // "paragraph" | "bullet"
    length:       "medium",     // "short" | "medium" | "long"
    method:       "abstractive",// "abstractive" | "extractive"
    lastSummary:  "",
    isLoading:    false,
};

// ═══════════════════════════════════════════════════════════════════
//  Initialization
// ═══════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initTextInput();
    initFileUpload();
    initSettings();
    initSummarize();
    initOutputActions();
    initDarkMode();
    initHistory();
    loadHistory();
});

// ═══════════════════════════════════════════════════════════════════
//  Tab Switching
// ═══════════════════════════════════════════════════════════════════

function initTabs() {
    elements.tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.dataset.tab;
            state.activeTab = tabId;

            // Update tab buttons
            elements.tabBtns.forEach(b => {
                b.classList.toggle("active", b.dataset.tab === tabId);
                b.setAttribute("aria-selected", b.dataset.tab === tabId);
            });

            // Update tab content
            elements.tabContents.forEach(c => {
                c.classList.toggle("active", c.id === tabId);
            });

            updateSummarizeButton();
        });
    });
}

// ═══════════════════════════════════════════════════════════════════
//  Text Input & Word Count
// ═══════════════════════════════════════════════════════════════════

function initTextInput() {
    elements.textInput.addEventListener("input", () => {
        const text = elements.textInput.value.trim();
        const wordCount = text ? text.split(/\s+/).filter(w => w.length > 0).length : 0;
        elements.wordCountDisplay.textContent = `${wordCount} word${wordCount !== 1 ? "s" : ""}`;
        updateSummarizeButton();
    });
}

// ═══════════════════════════════════════════════════════════════════
//  File Upload (Click + Drag & Drop)
// ═══════════════════════════════════════════════════════════════════

function initFileUpload() {
    // Click to upload
    elements.dropZone.addEventListener("click", () => {
        elements.fileInput.click();
    });

    elements.fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // Drag & Drop
    elements.dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        elements.dropZone.classList.add("drag-over");
    });

    elements.dropZone.addEventListener("dragleave", () => {
        elements.dropZone.classList.remove("drag-over");
    });

    elements.dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        elements.dropZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Remove file
    elements.removeFileBtn.addEventListener("click", () => {
        clearFile();
    });
}

function handleFile(file) {
    const allowedTypes = [".pdf", ".docx", ".txt"];
    const ext = "." + file.name.split(".").pop().toLowerCase();

    if (!allowedTypes.includes(ext)) {
        showToast("Unsupported file type. Please upload PDF, DOCX, or TXT.", "error");
        return;
    }

    if (file.size > 16 * 1024 * 1024) {
        showToast("File is too large. Maximum size is 16 MB.", "error");
        return;
    }

    state.selectedFile = file;
    elements.fileName.textContent = file.name;
    elements.fileInfo.style.display = "flex";
    elements.dropZone.style.display = "none";
    updateSummarizeButton();
}

function clearFile() {
    state.selectedFile = null;
    elements.fileInput.value = "";
    elements.fileName.textContent = "";
    elements.fileInfo.style.display = "none";
    elements.dropZone.style.display = "flex";
    updateSummarizeButton();
}

// ═══════════════════════════════════════════════════════════════════
//  Settings (Radio Cards)
// ═══════════════════════════════════════════════════════════════════

function initSettings() {
    // Generic radio group handler
    function setupRadioGroup(cards, stateKey) {
        cards.forEach(card => {
            card.addEventListener("click", () => {
                cards.forEach(c => c.classList.remove("active"));
                card.classList.add("active");
                const input = card.querySelector("input[type='radio']");
                if (input) {
                    input.checked = true;
                    state[stateKey] = input.value;
                }
            });
        });
    }

    setupRadioGroup(elements.formatOptions, "summaryType");
    setupRadioGroup(elements.lengthOptions, "length");
    setupRadioGroup(elements.methodOptions, "method");
}

// ═══════════════════════════════════════════════════════════════════
//  Summarize Button
// ═══════════════════════════════════════════════════════════════════

function updateSummarizeButton() {
    let hasInput = false;

    if (state.activeTab === "text-tab") {
        const text = elements.textInput.value.trim();
        hasInput = text.split(/\s+/).filter(w => w.length > 0).length >= 10;
    } else {
        hasInput = state.selectedFile !== null;
    }

    elements.summarizeBtn.disabled = !hasInput;
}

function initSummarize() {
    elements.summarizeBtn.addEventListener("click", performSummarization);
}

async function performSummarization() {
    if (state.isLoading) return;

    state.isLoading = true;
    showLoading(true);

    try {
        let response;

        if (state.activeTab === "text-tab") {
            // ── Send text as JSON ──
            const text = elements.textInput.value.trim();
            response = await fetch(`${API_BASE}/summarize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text: text,
                    summary_type: state.summaryType,
                    length: state.length,
                    method: state.method,
                }),
            });

        } else {
            // ── Send file as FormData ──
            const formData = new FormData();
            formData.append("file", state.selectedFile);
            formData.append("summary_type", state.summaryType);
            formData.append("length", state.length);
            formData.append("method", state.method);

            response = await fetch(`${API_BASE}/summarize`, {
                method: "POST",
                body: formData,
            });
        }

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Summarization failed.");
        }

        // Display result
        displayResult(data);
        showToast("Summary generated successfully!", "success");

        // Refresh history
        loadHistory();

    } catch (err) {
        console.error("Summarization error:", err);
        showToast(err.message || "Something went wrong. Please try again.", "error");
    } finally {
        state.isLoading = false;
        showLoading(false);
    }
}

// ═══════════════════════════════════════════════════════════════════
//  Display Result
// ═══════════════════════════════════════════════════════════════════

function displayResult(data) {
    state.lastSummary = data.summary;

    // Show output section
    elements.outputSection.style.display = "block";

    // Scroll to output
    setTimeout(() => {
        elements.outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);

    // Set summary text
    elements.summaryOutput.textContent = data.summary;

    // Set meta badges
    elements.outputMethod.textContent = data.method;
    elements.outputStats.textContent = `${data.word_count_original} → ${data.word_count_summary} words`;
}

// ═══════════════════════════════════════════════════════════════════
//  Output Actions (Copy / Download)
// ═══════════════════════════════════════════════════════════════════

function initOutputActions() {
    // Copy to clipboard
    elements.copyBtn.addEventListener("click", async () => {
        if (!state.lastSummary) return;
        try {
            await navigator.clipboard.writeText(state.lastSummary);
            showToast("Copied to clipboard!", "success");
        } catch {
            // Fallback
            const ta = document.createElement("textarea");
            ta.value = state.lastSummary;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            showToast("Copied to clipboard!", "success");
        }
    });

    // Download as TXT
    elements.downloadTxtBtn.addEventListener("click", () => {
        if (!state.lastSummary) return;
        downloadFile(state.lastSummary, "summarify-summary.txt", "text/plain");
        showToast("Downloaded as TXT!", "success");
    });

    // Download as PDF (uses browser print as a simple approach)
    elements.downloadPdfBtn.addEventListener("click", () => {
        if (!state.lastSummary) return;
        downloadAsPDF(state.lastSummary);
        showToast("PDF download initiated!", "success");
    });
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function downloadAsPDF(text) {
    // Create a printable window for PDF download
    const printWindow = window.open("", "_blank");
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Summarify — Summary</title>
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    padding: 40px;
                    line-height: 1.8;
                    color: #1a1a1a;
                    max-width: 700px;
                    margin: 0 auto;
                }
                h1 {
                    color: #6c63ff;
                    font-size: 1.5rem;
                    margin-bottom: 8px;
                }
                .meta { color: #888; font-size: 0.85rem; margin-bottom: 24px; }
                .content {
                    white-space: pre-wrap;
                    background: #f8f9fa;
                    padding: 24px;
                    border-radius: 8px;
                    border-left: 4px solid #6c63ff;
                }
            </style>
        </head>
        <body>
            <h1>Summarify — Summary</h1>
            <p class="meta">Generated on ${new Date().toLocaleString()}</p>
            <div class="content">${escapeHTML(text)}</div>
            <script>window.onload = () => { window.print(); }<\/script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// ═══════════════════════════════════════════════════════════════════
//  Loading Overlay
// ═══════════════════════════════════════════════════════════════════

function showLoading(show) {
    elements.loadingOverlay.style.display = show ? "flex" : "none";
}

// ═══════════════════════════════════════════════════════════════════
//  Toast Notification
// ═══════════════════════════════════════════════════════════════════

let toastTimeout = null;

function showToast(message, type = "") {
    clearTimeout(toastTimeout);
    elements.toast.textContent = message;
    elements.toast.className = "toast" + (type ? ` ${type}` : "");

    // Force reflow for re-animation
    void elements.toast.offsetWidth;
    elements.toast.classList.add("show");

    toastTimeout = setTimeout(() => {
        elements.toast.classList.remove("show");
    }, 3500);
}

// ═══════════════════════════════════════════════════════════════════
//  Dark Mode
// ═══════════════════════════════════════════════════════════════════

function initDarkMode() {
    // Check saved preference or system preference
    const saved = localStorage.getItem("summarify-dark-mode");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

    if (saved === "true" || (saved === null && prefersDark)) {
        document.body.classList.add("dark");
        updateDarkModeIcons(true);
    }

    elements.darkModeToggle.addEventListener("click", () => {
        const isDark = document.body.classList.toggle("dark");
        localStorage.setItem("summarify-dark-mode", isDark);
        updateDarkModeIcons(isDark);
    });
}

function updateDarkModeIcons(isDark) {
    elements.iconSun.style.display = isDark ? "none" : "block";
    elements.iconMoon.style.display = isDark ? "block" : "none";
}

// ═══════════════════════════════════════════════════════════════════
//  History
// ═══════════════════════════════════════════════════════════════════

function initHistory() {
    elements.clearHistoryBtn.addEventListener("click", async () => {
        if (!confirm("Clear all summary history?")) return;
        try {
            await fetch(`${API_BASE}/history`, { method: "DELETE" });
            loadHistory();
            showToast("History cleared.", "success");
        } catch (err) {
            showToast("Failed to clear history.", "error");
        }
    });
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/history`);
        const data = await response.json();

        if (data.success && data.history.length > 0) {
            renderHistory(data.history);
        } else {
            elements.historyList.innerHTML = `
                <div class="empty-state">
                    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="8" y="6" width="32" height="36" rx="4"/>
                        <line x1="16" y1="14" x2="32" y2="14"/>
                        <line x1="16" y1="22" x2="28" y2="22"/>
                        <line x1="16" y1="30" x2="24" y2="30"/>
                    </svg>
                    <p>No summaries yet. Create your first one above!</p>
                </div>`;
        }
    } catch {
        // Backend might not be running; show empty state silently
        elements.historyList.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="8" y="6" width="32" height="36" rx="4"/>
                    <line x1="16" y1="14" x2="32" y2="14"/>
                    <line x1="16" y1="22" x2="28" y2="22"/>
                    <line x1="16" y1="30" x2="24" y2="30"/>
                </svg>
                <p>No summaries yet. Create your first one above!</p>
            </div>`;
    }
}

function renderHistory(items) {
    elements.historyList.innerHTML = items.map(item => {
        const date = new Date(item.created_at).toLocaleString();
        const preview = item.summary.substring(0, 120) + (item.summary.length > 120 ? "…" : "");

        return `
        <div class="history-item" data-id="${item.id}">
            <div class="history-item-content">
                <div class="history-item-summary">${escapeHTML(preview)}</div>
                <div class="history-item-meta">
                    <span>${item.summary_type} · ${item.length}</span>
                    <span>${item.method}</span>
                    <span>${item.word_count_original} → ${item.word_count_summary} words</span>
                    <span>${date}</span>
                </div>
            </div>
            <button class="history-delete-btn" title="Delete" onclick="deleteHistoryItem('${item.id}')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
            </button>
        </div>`;
    }).join("");
}

async function deleteHistoryItem(id) {
    try {
        await fetch(`${API_BASE}/history/${id}`, { method: "DELETE" });
        loadHistory();
        showToast("History item deleted.", "success");
    } catch {
        showToast("Failed to delete item.", "error");
    }
}
