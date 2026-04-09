"""
app.py - Flask Backend for Summarify
Main application server with API endpoints for text summarization.
"""

import os
import uuid
import sqlite3
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from summarizer import summarize, get_word_count, preprocess_text
from file_handler import extract_text_from_file, allowed_file

# ─── App Configuration ───────────────────────────────────────────────

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the frontend

# Upload folder configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "summarify.db")


# ─── Database Setup ──────────────────────────────────────────────────

def init_db():
    """Initialize SQLite database for storing summary history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id TEXT PRIMARY KEY,
            original_text TEXT NOT NULL,
            summary TEXT NOT NULL,
            summary_type TEXT NOT NULL,
            length TEXT NOT NULL,
            method TEXT NOT NULL,
            word_count_original INTEGER,
            word_count_summary INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# Initialize DB on startup
init_db()


def save_to_history(data: dict) -> str:
    """Save a summary to the history database."""
    summary_id = str(uuid.uuid4())[:8]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (id, original_text, summary, summary_type, length, method,
                             word_count_original, word_count_summary, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        summary_id,
        data.get("original_text", "")[:500],  # Store first 500 chars
        data.get("summary", ""),
        data.get("summary_type", "paragraph"),
        data.get("length", "medium"),
        data.get("method", "abstractive"),
        data.get("word_count_original", 0),
        data.get("word_count_summary", 0),
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()
    return summary_id


def get_history() -> list:
    """Retrieve all summary history, most recent first."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_history_item(item_id: str) -> bool:
    """Delete a single history item by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE id = ?", (item_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def clear_all_history() -> int:
    """Delete all history items. Returns count of deleted rows."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


# ─── API Routes ──────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Summarify backend is running!"})


@app.route("/api/summarize", methods=["POST"])
def summarize_text():
    """
    Main summarization endpoint.
    
    Accepts either:
    - JSON body with 'text' field
    - Multipart form with 'file' field
    
    Additional fields:
    - summary_type: 'bullet' or 'paragraph' (default: 'paragraph')
    - length: 'short', 'medium', or 'long' (default: 'medium')
    - method: 'extractive' or 'abstractive' (default: 'abstractive')
    """
    text = None
    summary_type = "paragraph"
    length = "medium"
    method = "abstractive"

    # ── Handle file upload ──
    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file type. Please upload PDF, DOCX, or TXT."}), 400

        # Save file temporarily
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(file_path)

        try:
            text = extract_text_from_file(file_path)
        except (ValueError, FileNotFoundError) as e:
            return jsonify({"error": str(e)}), 400
        finally:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)

        # Get form fields
        summary_type = request.form.get("summary_type", "paragraph")
        length = request.form.get("length", "medium")
        method = request.form.get("method", "abstractive")

    # ── Handle JSON text input ──
    elif request.is_json:
        data = request.get_json()
        text = data.get("text", "").strip()
        summary_type = data.get("summary_type", "paragraph")
        length = data.get("length", "medium")
        method = data.get("method", "abstractive")

    # ── Handle form data without file ──
    elif request.form:
        text = request.form.get("text", "").strip()
        summary_type = request.form.get("summary_type", "paragraph")
        length = request.form.get("length", "medium")
        method = request.form.get("method", "abstractive")

    else:
        return jsonify({"error": "No input provided. Send text or upload a file."}), 400

    # Validate input
    if not text or not text.strip():
        return jsonify({"error": "No text content found. Please enter text or upload a valid file."}), 400

    # Validate parameters
    if summary_type not in ("bullet", "paragraph"):
        summary_type = "paragraph"
    if length not in ("short", "medium", "long"):
        length = "medium"
    if method not in ("extractive", "abstractive"):
        method = "abstractive"

    # ── Perform summarization ──
    try:
        result = summarize(
            text=text,
            summary_type=summary_type,
            length=length,
            method=method,
        )

        # Save to history
        history_data = {
            "original_text": text,
            "summary": result["summary"],
            "summary_type": summary_type,
            "length": length,
            "method": method,
            "word_count_original": result["word_count_original"],
            "word_count_summary": result["word_count_summary"],
        }
        summary_id = save_to_history(history_data)

        return jsonify({
            "success": True,
            "id": summary_id,
            "summary": result["summary"],
            "word_count_original": result["word_count_original"],
            "word_count_summary": result["word_count_summary"],
            "method": result["method"],
            "summary_type": summary_type,
            "length": length,
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"[!] Summarization error: {e}")
        return jsonify({"error": f"Summarization failed: {str(e)}"}), 500


@app.route("/api/history", methods=["GET"])
def get_summary_history():
    """Retrieve summary history."""
    history = get_history()
    return jsonify({"success": True, "history": history})


@app.route("/api/history/<item_id>", methods=["DELETE"])
def delete_history(item_id):
    """Delete a specific history item."""
    if delete_history_item(item_id):
        return jsonify({"success": True, "message": "History item deleted."})
    return jsonify({"error": "Item not found."}), 404


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    """Clear all history."""
    count = clear_all_history()
    return jsonify({"success": True, "message": f"Cleared {count} history items."})


@app.route("/api/word-count", methods=["POST"])
def word_count():
    """Get the word count of provided text."""
    data = request.get_json()
    text = data.get("text", "")
    count = get_word_count(text) if text else 0
    return jsonify({"word_count": count})


# ─── Run Server ──────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("[*] Summarify backend starting...")
    print(f"[*] API available at: http://localhost:{port}")
    print("-" * 45)
    app.run(debug=True, host="0.0.0.0", port=port)
