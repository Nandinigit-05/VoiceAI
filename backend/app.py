from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import speech
import google.generativeai as genai
import os
from dotenv import load_dotenv

from analysis.filler_words import count_filler_words
from analysis.speaking_speed import calculate_wpm
from analysis.scoring import confidence_score, clarity_score
import json

load_dotenv()

# Gemini API configuration (optional - app works without it)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("[Gemini] API configured successfully")
    except Exception as e:
        print(f"[Gemini] Configuration error: {e}")
else:
    print("[Gemini] API key not found - using fallback feedback only")

app = Flask(__name__)

# CORS configuration: Allow requests from Vite dev server and other localhost ports
# Frontend runs on http://localhost:8080 or http://127.0.0.1:8080
# Backend runs on http://127.0.0.1:5000
CORS(app, origins=[
    "http://localhost:8080",  # Vite dev server (custom port)
    "http://127.0.0.1:8080",   # Vite dev server (custom port, 127.0.0.1)
    "http://localhost:5173",   # Vite default port
    "http://127.0.0.1:5173",   # Vite default port (127.0.0.1)
    "http://localhost:3000",   # Common React dev port
    "http://127.0.0.1:3000",   # Common React dev port (127.0.0.1)
], supports_credentials=True, allow_headers=["Content-Type"])

AUDIO_FOLDER = "audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# ---------------- Speech to Text ----------------
def speech_to_text(audio_path):
    client = speech.SpeechClient()

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        language_code="en-US",
        enable_automatic_punctuation=True,
        model="latest_long"
    )

    response = client.recognize(config=config, audio=audio)

    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "

    return transcript.strip()

def _default_feedback_structure():
    """
    Base structure for AI feedback used by both Gemini and fallback:
    {
      "overall_assessment": string,
      "areas_to_improve": [string, ...],
      "actionable_tips": [string, ...],
      "improved_sample_answer": string
    }
    """
    return {
        "overall_assessment": "",
        "areas_to_improve": [],
        "actionable_tips": [],
        "improved_sample_answer": "",
    }


# ---------------- Fallback Feedback Generator ----------------
def generate_fallback_feedback(transcript, metrics, filler_data):
    """
    Generate structured coaching feedback without Gemini API.
    This NEVER repeats the original transcript and returns plain text only.
    """
    wpm = metrics["wpm"]
    confidence = metrics["confidence"]
    clarity = metrics["clarity"]
    filler_total = metrics["filler_total"]
    total_words = metrics["total_words"]

    feedback = _default_feedback_structure()

    # Overall Assessment
    if confidence >= 80 and clarity >= 80 and filler_total <= 2:
        feedback["overall_assessment"] = (
            "Your response shows strong interview communication skills with a clear structure, "
            "steady pacing, and minimal distracting fillers. You are already communicating at a "
            "level that would feel confident and polished to many interviewers."
        )
    elif confidence >= 60 and clarity >= 60:
        feedback["overall_assessment"] = (
            "Your response has a solid foundation with generally clear ideas and reasonable pacing, "
            "but there are noticeable gaps in structure and delivery that, once refined, will make "
            "your answers sound much more confident and compelling."
        )
    else:
        feedback["overall_assessment"] = (
            "Your response currently feels rough and a bit hard to follow. With focused practice "
            "on structure, pacing, and removing filler words, you can make a significant jump in "
            "how professional and confident you sound in interviews."
        )

    # Areas to Improve (each as its own bullet item)
    areas = []
    if wpm < 100:
        areas.append(
            "Your speaking pace is slower than ideal, which can make you sound unsure or cause the interviewer to lose focus."
        )
    elif wpm > 180:
        areas.append(
            "You speak too quickly at times, which makes it harder for the interviewer to absorb your key points."
        )

    if filler_total > 2:
        areas.append(
            f"You rely on filler words (like 'um', 'uh', or 'like') about {filler_total} times, which weakens your professional presence."
        )

    if clarity < 70:
        areas.append(
            "Your answer lacks a clear beginning, middle, and end, which makes your main message harder to follow."
        )

    if total_words < 50:
        areas.append(
            "Your answer is quite brief and does not provide enough concrete examples or detail to fully showcase your skills."
        )

    if not areas:
        areas.append(
            "You have a good foundation, but you would still benefit from tightening your structure and being more intentional about your wording."
        )

    feedback["areas_to_improve"] = areas

    # Actionable Tips (each as its own bullet item)
    tips = []
    if wpm < 100:
        tips.append(
            "Practice answering common interview questions while gradually increasing your pace; aim for a natural, conversational speed rather than reading slowly."
        )
    elif wpm > 180:
        tips.append(
            "Intentionally pause for one or two seconds after key points; this slows you down and gives your answers more impact."
        )

    if filler_total > 2:
        tips.append(
            "Record yourself answering questions and deliberately replace filler words with short pauses; silence feels more confident than repeated 'um' or 'like'."
        )

    if clarity < 70:
        tips.append(
            "Use the STAR method (Situation, Task, Action, Result) to structure each answer so the interviewer can easily follow your story."
        )

    if total_words < 50:
        tips.append(
            "Expand your answers by adding one concrete example and one measurable result for each main point you want to highlight."
        )

    if not tips:
        tips.append(
            "Continue practicing out loud and reviewing your recordings; focus on sounding clear, calm, and intentional with every sentence."
        )

    feedback["actionable_tips"] = tips

    # Improved Sample Answer: generic, not repeating the original transcript
    feedback["improved_sample_answer"] = (
        "In a real interview, a stronger version of your answer might sound like this:\n\n"
        "\"In my previous role, I was responsible for leading a project where our team needed to "
        "improve deployment reliability. First, I analyzed our existing process and identified the "
        "main failure points. Then I coordinated with engineering and QA to introduce automated "
        "checks and a clearer rollback plan. As a result, we reduced deployment-related incidents "
        "by about 40% over three months. This experience taught me how to stay calm under pressure "
        "and communicate clearly with both technical and non-technical stakeholders.\"\n\n"
        "Use this as a model: clear context, specific actions, and a measurable result, all delivered "
        "in a steady, confident tone."
    )

    return feedback

def _parse_gemini_json(text: str):
    """
    Parse Gemini's response as JSON, enforcing the expected structure.
    Strips any accidental code fences and ignores markdown.
    """
    if not text:
        return None

    raw = text.strip()
    # Remove Markdown-style fences if present
    if raw.startswith("```"):
        raw = raw.lstrip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        if "```" in raw:
            raw = raw.split("```", 1)[0]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"[Gemini JSON Parse Error] {e}")
        return None

    # Ensure the expected keys exist; fall back to defaults if missing
    base = _default_feedback_structure()
    if isinstance(data, dict):
        for key in base.keys():
            if key in data and data[key] is not None:
                base[key] = data[key]
    return base


# ---------------- Gemini Feedback (Optional) ----------------
def get_ai_feedback(transcript, metrics, filler_data):
    """
    Attempt to get Gemini feedback as strict JSON.
    Returns a dict matching _default_feedback_structure() or None on any error.
    """
    # Skip if API key not configured
    if not GEMINI_API_KEY:
        return None

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        prompt = f"""
You are an interview communication coach.
Your task is to evaluate a candidate's spoken answer for an interview and respond
STRICTLY as JSON with this exact structure:

{{
  "overall_assessment": string,
  "areas_to_improve": string[],
  "actionable_tips": string[],
  "improved_sample_answer": string
}}

Rules:
- Respond with VALID JSON ONLY. No markdown, no code fences, no headings, no explanations.
- Do NOT repeat or quote the original transcript.
- Do NOT include symbols like #, *, -, or bullet markers in the text.
- Each item in "areas_to_improve" and "actionable_tips" must be a full sentence focused on one idea.
- Focus on interview performance: clarity, structure, confidence, pacing, relevance, and professionalism.
- Tone must be professional, constructive, and coaching-oriented.

Candidate transcript:
\"\"\"{transcript}\"\"\"
"""

        response = model.generate_content(prompt)
        feedback = _parse_gemini_json(response.text)
        return feedback
    except Exception as e:
        # Log error to console only (not exposed to frontend)
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"[Gemini API Error] {error_type}: {error_msg}")
        if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            print("[Gemini API] Quota limit reached - using fallback feedback")
        return None

# ---------------- Routes ----------------
@app.route("/analyze", methods=["POST"])
def analyze():
    audio_file = request.files["audio"]
    duration = float(request.form.get("duration", 60))  # seconds

    audio_path = os.path.join(AUDIO_FOLDER, "input.wav")
    audio_file.save(audio_path)

    # Core analysis - ALWAYS computed locally (no Gemini dependency)
    transcript = speech_to_text(audio_path)

    filler = count_filler_words(transcript)
    wpm = calculate_wpm(transcript, duration)

    sentence_count = transcript.count(".")
    confidence = confidence_score(wpm, filler["total"])
    clarity = clarity_score(sentence_count, filler["total"])

    # Build metrics dictionary (always present)
    metrics = {
        "wpm": wpm,
        "confidence": confidence,
        "clarity": clarity,
        "total_words": len(transcript.split()),
        "filler_total": filler["total"],
        "filler_breakdown": filler["per_word"]
    }

    # Try Gemini feedback (optional - never fails the endpoint)
    gemini_feedback = get_ai_feedback(transcript, metrics, filler)
    
    # Use Gemini feedback if available, otherwise use fallback
    if gemini_feedback:
        feedback = gemini_feedback
        print("[Feedback] Using Gemini AI feedback")
    else:
        feedback = generate_fallback_feedback(transcript, metrics, filler)
        print("[Feedback] Using fallback feedback (Gemini unavailable)")

    # ALWAYS return valid JSON with all required fields
    return jsonify({
        "raw_transcript": transcript,
        "metrics": metrics,
        "ai_feedback": feedback
    })

@app.route("/health")
def health():
    return {"status": "OK"}

if __name__ == "__main__":
    app.run(debug=True)
