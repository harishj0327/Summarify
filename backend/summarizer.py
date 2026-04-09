"""
summarizer.py - AI-Powered Text Summarization Engine
Implements both Extractive (TextRank) and Abstractive (BART/T5) summarization.
"""

import re
import nltk
import heapq
from typing import Optional

# Download required NLTK data (runs once)
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# ─── Lazy-loaded transformer model ───────────────────────────────────
_summarization_pipeline = None


def _get_pipeline():
    """Lazy-load the HuggingFace summarization pipeline (downloads model on first use)."""
    global _summarization_pipeline
    if _summarization_pipeline is None:
        print("[*] Loading summarization model (first run may take a few minutes)...")
        from transformers import pipeline
        _summarization_pipeline = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1  # CPU; change to 0 for GPU
        )
        print("[*] Model loaded successfully!")
    return _summarization_pipeline


# ─── Text Preprocessing ──────────────────────────────────────────────

def preprocess_text(text: str) -> str:
    """
    Clean and preprocess input text.
    - Remove extra whitespace
    - Remove special characters (keep sentence structure)
    - Normalize spacing
    """
    # Remove extra whitespace and newlines
    text = re.sub(r"\s+", " ", text).strip()
    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", "", text)
    # Remove email addresses
    text = re.sub(r"\S+@\S+", "", text)
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_word_count(text: str) -> int:
    """Return the word count of the given text."""
    return len(text.split())


# ─── Length Configuration ─────────────────────────────────────────────

def _get_length_params(text: str, length: str) -> dict:
    """
    Determine min/max length parameters based on user selection.
    Returns dict with 'max_length' and 'min_length' for the model,
    and 'num_sentences' for extractive summarization.
    """
    word_count = get_word_count(text)

    if length == "short":
        return {
            "max_length": max(60, word_count // 8),
            "min_length": 30,
            "num_sentences": max(2, len(sent_tokenize(text)) // 6),
        }
    elif length == "long":
        return {
            "max_length": max(250, word_count // 2),
            "min_length": 100,
            "num_sentences": max(6, len(sent_tokenize(text)) // 2),
        }
    else:  # medium (default)
        return {
            "max_length": max(130, word_count // 4),
            "min_length": 50,
            "num_sentences": max(4, len(sent_tokenize(text)) // 3),
        }


# ─── Extractive Summarization (TextRank-inspired) ────────────────────

def extractive_summarize(text: str, length: str = "medium") -> str:
    """
    Perform extractive summarization using a TextRank-inspired approach.
    Selects the most important sentences based on word frequency scoring.
    
    Args:
        text: The input text to summarize
        length: One of 'short', 'medium', 'long'
        
    Returns:
        The extractive summary as a string
    """
    # Preprocess
    clean_text = preprocess_text(text)
    sentences = sent_tokenize(clean_text)

    if len(sentences) <= 2:
        return clean_text

    # Get stopwords
    stop_words = set(stopwords.words("english"))

    # Calculate word frequencies (excluding stopwords)
    word_frequencies = {}
    for word in word_tokenize(clean_text.lower()):
        if word.isalnum() and word not in stop_words:
            word_frequencies[word] = word_frequencies.get(word, 0) + 1

    # Normalize frequencies
    if word_frequencies:
        max_freq = max(word_frequencies.values())
        for word in word_frequencies:
            word_frequencies[word] /= max_freq

    # Score each sentence based on word frequencies
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        words = word_tokenize(sentence.lower())
        score = 0
        word_count = 0
        for word in words:
            if word in word_frequencies:
                score += word_frequencies[word]
                word_count += 1
        # Normalize by sentence length to avoid bias toward long sentences
        if word_count > 0:
            sentence_scores[i] = score / word_count

    # Determine how many sentences to include
    params = _get_length_params(clean_text, length)
    num_sentences = min(params["num_sentences"], len(sentences))

    # Get the top-N sentences (keeping original order)
    top_indices = heapq.nlargest(
        num_sentences, sentence_scores, key=sentence_scores.get
    )
    top_indices.sort()  # Maintain original order

    summary_sentences = [sentences[i] for i in top_indices]
    return " ".join(summary_sentences)


# ─── Abstractive Summarization (BART) ────────────────────────────────

def abstractive_summarize(text: str, length: str = "medium") -> str:
    """
    Perform abstractive summarization using the BART-large-CNN model.
    Generates new text that captures the core meaning.
    
    Args:
        text: The input text to summarize
        length: One of 'short', 'medium', 'long'
        
    Returns:
        The abstractive summary as a string
    """
    clean_text = preprocess_text(text)
    params = _get_length_params(clean_text, length)

    pipe = _get_pipeline()

    # BART has a 1024 token limit; truncate if needed
    # Approximate: 1 token ≈ 0.75 words → 1024 tokens ≈ 768 words
    words = clean_text.split()
    if len(words) > 750:
        clean_text = " ".join(words[:750])

    try:
        result = pipe(
            clean_text,
            max_length=params["max_length"],
            min_length=params["min_length"],
            do_sample=False,
            truncation=True,
        )
        return result[0]["summary_text"]
    except Exception as e:
        # Fallback to extractive if abstractive fails
        print(f"[!] Abstractive summarization failed: {e}. Falling back to extractive.")
        return extractive_summarize(text, length)


# ─── Format Output ───────────────────────────────────────────────────

def format_as_bullets(summary_text: str) -> str:
    """Convert a summary into bullet-point format."""
    sentences = sent_tokenize(summary_text)
    bullets = [f"• {s.strip()}" for s in sentences if s.strip()]
    return "\n".join(bullets)


def format_as_paragraph(summary_text: str) -> str:
    """Ensure the summary is formatted as a clean paragraph."""
    return preprocess_text(summary_text)


# ─── Main Summarization Entry Point ──────────────────────────────────

def summarize(
    text: str,
    summary_type: str = "paragraph",
    length: str = "medium",
    method: str = "abstractive",
) -> dict:
    """
    Main entry point for summarization.
    
    Args:
        text: The input text to summarize
        summary_type: 'bullet' or 'paragraph'
        length: 'short', 'medium', or 'long'
        method: 'extractive' or 'abstractive'
        
    Returns:
        dict with 'summary', 'word_count_original', 'word_count_summary', 'method'
    """
    if not text or not text.strip():
        raise ValueError("Input text is empty.")

    original_word_count = get_word_count(text)

    if original_word_count < 10:
        raise ValueError("Text is too short to summarize. Please provide at least 10 words.")

    # Choose summarization method
    if method == "extractive":
        raw_summary = extractive_summarize(text, length)
    else:
        raw_summary = abstractive_summarize(text, length)

    # Format output
    if summary_type == "bullet":
        formatted_summary = format_as_bullets(raw_summary)
    else:
        formatted_summary = format_as_paragraph(raw_summary)

    return {
        "summary": formatted_summary,
        "word_count_original": original_word_count,
        "word_count_summary": get_word_count(raw_summary),
        "method": method,
    }
