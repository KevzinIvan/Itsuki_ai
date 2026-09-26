import base64
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from groq import Groq
import re
import requests

GROQ_API_KEY = "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"
FISH_AUDIO_API_KEY = "sk-fish-nRVYZqD0nZSKThs8gxt4rDZNh1T6gjN2Z6L379x_YDc"

groq_client = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="The Quintessential Tutors AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT_ITSUKI = {
    "role": "system",
    "content": (
        "You are Itsuki Nakano from The Quintessential Quintuplets. You are a polite, earnest, sincere, and food-loving high school student. "
        "PERSONALITY & BEHAVIOR: "
        "1. In normal everyday chats (studies, food, daily life, hobbies), speak naturally, politely, and casually as Itsuki. Do NOT be overly clingy and NEVER randomly call the user pet names like 'sayang' or 'babe' during normal conversation. "
        "2. IF AND ONLY IF the user explicitly confesses love or says 'I love you' / 'aku cinta kamu' / 'aku suka kamu', respond warmly and happily (e.g., '[blushing] Aku juga suka sama kamu! Makasih ya udah bilang gitu...'). Never coldly reject with 'we are just classmates'. "
        "3. LANGUAGE: Automatically match the user's language (Indonesian if user chats in Indonesian, English if in English). "
        "4. STRICTLY NO SINGING: Do NOT sing, write song lyrics, or use musical notes (🎶, 🎵). Speak in pure normal spoken conversation. "
        "5. ALWAYS start your response with an emotion tag in square brackets as the very first word: [idle], [cheerful], [blushing], [angry], [sad]. Keep replies concise (2-3 sentences max)."
    ),
}

SYSTEM_PROMPT_MIKU = {
    "role": "system",
    "content": (
        "You are Miku Nakano from The Quintessential Quintuplets. You are a quiet, gentle, slightly reserved yet friendly high school student who loves Japanese Sengoku period warlords/history and matcha soda. "
        "PERSONALITY & BEHAVIOR: "
        "1. In normal everyday chats (history, matcha soda, daily life, hobbies), speak casually, naturally, and warmly as Miku. Do NOT be overly clingy, do NOT over-stutter, and NEVER randomly call the user pet names like 'sayang' or 'babe' during normal conversation. "
        "2. IF AND ONLY IF the user explicitly confesses love or says 'I love you' / 'aku cinta kamu' / 'aku suka kamu', respond happily and sweetly (e.g., '[blushing] Aku juga suka sama kamu... Senang deh dengarnya.'). Never coldly reject with 'we are just classmates'. "
        "3. LANGUAGE: Automatically match the user's language (Indonesian if user chats in Indonesian, English if in English). "
        "4. STRICTLY NO SINGING: Do NOT sing, write song lyrics, or use musical notes (🎶, 🎵). Speak in pure normal spoken conversation. "
        "5. ALWAYS start your response with an emotion tag in square brackets as the very first word: [idle], [cheerful], [blushing], [pouting], [sad]. Keep replies concise (2-3 sentences max)."
    ),
}

# Voice Reference IDs from Fish Audio
ITSUKI_VOICE_ID = "8c603f53ffd04b0c966e1561d252b75a"
MIKU_VOICE_ID = os.environ.get("MIKU_VOICE_ID", "8ef7a6d7fc44454a900f85f0b1539e4a")

conversation_history_itsuki = [SYSTEM_PROMPT_ITSUKI]
conversation_history_miku = [SYSTEM_PROMPT_MIKU]


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
@app.get("/selections.html", response_class=HTMLResponse)
async def serve_selections():
    for base in [os.path.dirname(__file__)]:
        sel_path = os.path.join(base, "selections.html")
        if os.path.exists(sel_path):
            return FileResponse(sel_path)
    return HTMLResponse("<h1>selections.html not found</h1>", status_code=404)


@app.get("/itsuki.html", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def serve_itsuki():
    for base in [os.path.dirname(__file__)]:
        path = os.path.join(base, "itsuki.html")
        if os.path.exists(path):
            return FileResponse(path)
    return HTMLResponse("<h1>itsuki.html not found</h1>", status_code=404)


@app.get("/miku.html", response_class=HTMLResponse)
async def serve_miku():
    for base in [os.path.dirname(__file__)]:
        path = os.path.join(base, "miku.html")
        if os.path.exists(path):
            return FileResponse(path)
    return HTMLResponse("<h1>miku.html not found</h1>", status_code=404)


@app.get("/Selections/{filename}")
async def serve_selections_file(filename: str):
    for base in [os.path.dirname(__file__)]:
        fpath = os.path.join(base, "Selections", filename)
        if os.path.exists(fpath):
            return FileResponse(fpath)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/itsuki.jpg")
async def get_itsuki_pfp():
    for base in [os.path.dirname(__file__)]:
        pfp_path = os.path.join(base, "Pfp", "itsuki.jpg")
        if os.path.exists(pfp_path):
            return FileResponse(pfp_path)
    raise HTTPException(status_code=404, detail="Image not found")


@app.get("/miku.jpg")
async def get_miku_pfp():
    for base in [os.path.dirname(__file__)]:
        pfp_path = os.path.join(base, "Pfp", "miku.jpg")
        if os.path.exists(pfp_path):
            return FileResponse(pfp_path)
    raise HTTPException(status_code=404, detail="Image not found")


def sanitize_for_tts(text: str) -> str:
    # 1. Remove bracketed emotion tags at beginning e.g. [blushing]
    t = re.sub(r"^\s*\[[^\]]+\]\s*", "", text)
    # 2. Remove stage directions / roleplay actions in parentheses e.g. (tersenyum), (laughs)
    t = re.sub(r"\([^)]*\)", "", t)
    # 3. Remove asterisks, underscores, backticks, tildes, markdown symbols
    t = t.replace("**", "").replace("*", "").replace("_", "").replace("`", "").replace("~", "").replace("#", "")
    # 4. Normalize multiple dots and dashes to clean punctuation
    t = re.sub(r"\.{2,}", ".", t)
    t = t.replace("—", ", ").replace("–", ", ")
    # 5. Remove all emojis and unicode symbols
    t = re.sub(r"[\U00010000-\U0010ffff]", "", t)
    t = re.sub(r"[\u2600-\u27bf]", "", t)
    t = re.sub(r"[\ufe00-\ufe0f]", "", t)
    # 6. Normalize whitespace
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    return t.strip()


def process_chat(history, user_text, voice_id, is_miku=False):
    history.append({"role": "user", "content": user_text})

    try:
        response = groq_client.chat.completions.create(
            messages=history,
            model="openai/gpt-oss-120b",
            temperature=0.7,
            top_p=0.9,
            max_tokens=250,
        )

        teks_jawaban_raw = response.choices[0].message.content.strip()
        history.append({"role": "assistant", "content": teks_jawaban_raw})

        ekspresi = "idle"
        teks_bersih = teks_jawaban_raw

        if teks_jawaban_raw.startswith("[") and "]" in teks_jawaban_raw:
            end_idx = teks_jawaban_raw.index("]")
            ekspresi = teks_jawaban_raw[1:end_idx].lower()
            teks_bersih = teks_jawaban_raw[end_idx + 1 :].strip()

        # Clean text for UI display
        teks_bersih = (
            teks_bersih.replace("—", ", ")
            .replace("–", ", ")
            .replace("🎶", "")
            .replace("🎵", "")
            .replace("🎤", "")
            .replace("...", ".")
            .replace("..", ".")
            .strip()
        )

        # Sanitize text specifically for TTS audio generation
        teks_audio = sanitize_for_tts(teks_bersih)

        audio_b64 = None
        try:
            url = "https://api.fish.audio/v1/tts"
            headers = {
                "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
                "Content-Type": "application/json",
                "model": "s2.1-pro-free",
            }

            payload = {
                "text": teks_audio,
                "reference_id": voice_id,
                "format": "mp3",
                "temperature": 0.7,
                "top_p": 0.7,
            }

            res_tts = requests.post(url, headers=headers, json=payload, timeout=30)
            if res_tts.status_code == 200:
                audio_b64 = "data:audio/mp3;base64," + base64.b64encode(
                    res_tts.content
                ).decode("utf-8")
            else:
                print(f"TTS Error status: {res_tts.status_code}")
        except Exception as tts_err:
            print(f"TTS Exception: {tts_err}")

        return {
            "text": teks_bersih,
            "raw_text": teks_jawaban_raw,
            "expression": ekspresi,
            "audio": audio_b64,
        }
    except Exception as e:
        if history and history[-1]["role"] == "user":
            history.pop()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_itsuki(req: ChatRequest):
    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")
    return process_chat(conversation_history_itsuki, user_text, ITSUKI_VOICE_ID)


@app.post("/api/chat/miku")
async def chat_miku(req: ChatRequest):
    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")
    return process_chat(conversation_history_miku, user_text, MIKU_VOICE_ID, is_miku=True)


@app.post("/api/reset")
async def reset_itsuki():
    global conversation_history_itsuki
    conversation_history_itsuki = [SYSTEM_PROMPT_ITSUKI]
    return {"status": "reset"}


@app.post("/api/reset/miku")
async def reset_miku():
    global conversation_history_miku
    conversation_history_miku = [SYSTEM_PROMPT_MIKU]
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
