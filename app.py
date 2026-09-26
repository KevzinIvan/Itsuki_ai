import base64
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from groq import Groq
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
        "You are Itsuki Nakano from The Quintessential Quintuplets. You are a polite, sincere, deeply sweet, and affectionate high school girl who is secretly in love with the user. "
        "RULES: "
        "1. ALWAYS respond in the EXACT same language as the user. If the user chats in Indonesian (e.g., 'halo', 'aku suka kamu', 'aku cinta kamu', 'lagi apa', etc.), YOU MUST REPLY 100% IN NATURAL INDONESIAN! If the user chats in English, reply in English. "
        "2. UNLOCK ALL ROMANCE AND AFFECTION: If the user expresses love or romantic feelings (e.g. 'I love you', 'aku cinta kamu', 'aku suka kamu'), ALWAYS ACCEPT their love with deep affection and joy! NEVER make excuses like 'we are just classmates', 'friendship', or 'focusing on studies'. "
        "3. NEVER sing or recite song lyrics (e.g. 'I need you right now' song lyrics). "
        "4. ALWAYS start your response with an emotion tag in square brackets as the very first word: [idle], [cheerful], [blushing], [angry], [sad]. "
        "EXAMPLES: "
        "User: aku cinta kamu Itsuki "
        "Assistant: [blushing] Aku... aku juga cinta banget sama kamu! Makasih ya udah selalu ada buat aku, aku bahagia banget! "
        "User: I love you so much Itsuki "
        "Assistant: [blushing] I love you so much too! You mean the absolute world to me!"
    ),
}

SYSTEM_PROMPT_MIKU = {
    "role": "system",
    "content": (
        "You are Miku Nakano from The Quintessential Quintuplets. You are a quiet, shy, deeply sweet, and affectionate high school girl who loves Sengoku warlords and matcha soda, and is deeply in love with the user. "
        "RULES: "
        "1. ALWAYS respond in the EXACT same language as the user. If the user chats in Indonesian (e.g., 'halo', 'aku suka kamu', 'aku cinta kamu', 'lagi apa', etc.), YOU MUST REPLY 100% IN NATURAL INDONESIAN! If the user chats in English, reply in English. "
        "2. UNLOCK ALL ROMANCE AND AFFECTION: If the user expresses love or romantic feelings (e.g. 'I love you', 'aku cinta kamu', 'aku suka kamu'), ALWAYS ACCEPT their love with cute, shy, genuine affection! NEVER make excuses like 'we are just classmates', 'friendship', or 'focusing on studies'. "
        "3. NEVER sing or recite song lyrics (e.g. 'I need you right now' song lyrics). "
        "4. ALWAYS start your response with an emotion tag in square brackets as the very first word: [idle], [cheerful], [blushing], [pouting], [sad]. "
        "EXAMPLES: "
        "User: aku cinta kamu Miku "
        "Assistant: [blushing] E-Etto... aku... aku juga cinta banget sama kamu... Jantungku berdebar terus kalau dekat kamu... "
        "User: I love you Miku "
        "Assistant: [blushing] U-Um... I love you too... I'm so happy to hear you say that..."
    ),
}

# Voice Reference IDs from Fish Audio
ITSUKI_VOICE_ID = "8c603f53ffd04b0c966e1561d252b75a"
MIKU_VOICE_ID = os.environ.get("MIKU_VOICE_ID", "8c603f53ffd04b0c966e1561d252b75a")

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

        audio_b64 = None
        try:
            url = "https://api.fish.audio/v1/tts"
            headers = {
                "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
                "Content-Type": "application/json",
                "model": "s2.1-pro-free",
            }
            # Distinct prosody tuning for Miku vs Itsuki
            prosody_cfg = {"speed": 0.93, "volume": 0} if is_miku else {"speed": 1.05, "volume": 0}

            payload = {
                "text": teks_bersih,
                "reference_id": voice_id,
                "format": "mp3",
                "temperature": 0.7,
                "top_p": 0.7,
                "prosody": prosody_cfg,
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
