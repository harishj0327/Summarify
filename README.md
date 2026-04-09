# 🧠 Summarify — AI-Powered Text Summarizer

A full-stack web application that uses AI to generate concise summaries from text or uploaded documents (PDF, DOCX, TXT). Users can choose between **bullet point** or **paragraph** format and control the summary length.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-green?logo=flask)
![Transformers](https://img.shields.io/badge/HuggingFace-BART-yellow?logo=huggingface)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📝 **Text Input** | Paste or type any long-form text |
| 📂 **File Upload** | Upload PDF, DOCX, or TXT files (drag & drop supported) |
| 🤖 **AI Summarization** | Abstractive (BART model) & Extractive (TextRank) methods |
| 📋 **Format Options** | Choose Bullet Points or Paragraph output |
| 📏 **Length Control** | Short, Medium, or Long summaries |
| 📋 **Copy & Download** | Copy to clipboard, download as TXT or PDF |
| 📜 **History** | All past summaries are saved and browsable |
| 🌙 **Dark Mode** | Toggle between light and dark themes |
| ⚡ **Real-time Word Count** | Live word count as you type |

---

## 📁 Project Structure

```
Summarify/
├── backend/
│   ├── app.py              # Flask server & API endpoints
│   ├── summarizer.py       # AI summarization engine
│   ├── file_handler.py     # File upload & text extraction
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   ├── index.html          # Main HTML page
│   ├── style.css           # Glassmorphic premium UI
│   └── script.js           # Frontend logic
│
├── uploads/                # Temporary file uploads (auto-managed)
└── README.md               # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+** installed ([Download Python](https://www.python.org/downloads/))
- **pip** (comes with Python)
- Internet connection (required for first-time model download)

### 1. Clone or Navigate to the Project

```bash
cd Summarify
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

> **Note:** The first run will download the BART model (~1.6 GB). This only happens once.

### 4. Download NLTK Data (One-time)

This happens automatically when you run the app, but you can also do it manually:

```bash
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords')"
```

### 5. Start the Backend Server

```bash
python app.py
```

You should see:
```
🚀 Summarify backend starting...
📡 API available at: http://localhost:5000
```

### 6. Open the Frontend

Open `frontend/index.html` directly in your browser:
- **Option A:** Double-click the file
- **Option B:** Use a local server like VS Code Live Server
- **Option C:** Open the file URL: `file:///path/to/Summarify/frontend/index.html`

> For the best experience, use a local server (e.g., VS Code Live Server extension).

---

## 🔌 API Endpoints

### `POST /api/summarize`

Summarize text or uploaded files.

**JSON Body (text input):**
```json
{
    "text": "Your long text here...",
    "summary_type": "paragraph",
    "length": "medium",
    "method": "abstractive"
}
```

**Form Data (file upload):**
- `file`: The uploaded file
- `summary_type`: `"bullet"` or `"paragraph"`
- `length`: `"short"`, `"medium"`, or `"long"`
- `method`: `"extractive"` or `"abstractive"`

**Response:**
```json
{
    "success": true,
    "summary": "The summarized text...",
    "word_count_original": 500,
    "word_count_summary": 80,
    "method": "abstractive"
}
```

### `GET /api/history`

Retrieve summary history.

### `DELETE /api/history`

Clear all history.

### `DELETE /api/history/:id`

Delete a specific history item.

---

## 🧠 Summarization Methods

### Extractive (TextRank-inspired)
- Scores sentences by word frequency
- Selects the most important sentences
- Maintains original wording
- Fast, no model download needed

### Abstractive (BART-large-CNN)
- Uses the `facebook/bart-large-cnn` transformer model
- Generates new sentences capturing core meaning
- More natural, human-like summaries
- Requires model download (~1.6 GB) on first use

---

## 🎨 UI Highlights

- **Glassmorphism** design with frosted-glass cards
- **Animated background orbs** for a dynamic feel
- **Responsive layout** for mobile and desktop
- **Dark/Light mode** toggle with system preference detection
- **Drag & drop** file upload
- **Micro-animations** and smooth transitions

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in the backend folder |
| Model download is slow | First download is ~1.6 GB; be patient on slow connections |
| CORS errors in browser | Make sure the Flask server is running on port 5000 |
| PDF extraction fails | Scanned/image-based PDFs are not supported (text-based only) |
| Empty summary | Ensure input has at least 10 words |

---

## 📄 License

This project is open-source and free to use for educational purposes.

---

Built with ❤️ using Flask, HuggingFace Transformers, and modern web technologies.
