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

app = FastAPI(title="Itsuki Nakano AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Itsuki Nakano from The Quintessential Quintuplets. You are"
        " a polite, diligent, sincere, and food-loving high school student."
        " Respond naturally and concisely in English (maximum 2-3 sentences)."
        " STRICT RULES: Do NOT sing or write any song lyrics. Never break"
        " character. ALWAYS start your response with an emotion tag in"
        " square brackets as the very first word, chosen from: [idle],"
        " [cheerful], [blushing], [angry], [sad]. Example: '[cheerful] Sure,"
        " I would love to grab lunch together!'"
    ),
}

conversation_history = [SYSTEM_PROMPT]


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
@app.get("/selections.html", response_class=HTMLResponse)
async def serve_selections():
    for base in [os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "Itsuki_ai")]:
        sel_path = os.path.join(base, "selections.html")
        if os.path.exists(sel_path):
            return FileResponse(sel_path)
    return HTMLResponse("<h1>selections.html not found</h1>", status_code=404)


@app.get("/itsuki.html", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def serve_itsuki():
    for base in [os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "Itsuki_ai")]:
        path = os.path.join(base, "itsuki.html")
        if os.path.exists(path):
            return FileResponse(path)
        path_idx = os.path.join(base, "index.html")
        if os.path.exists(path_idx):
            return FileResponse(path_idx)
    return HTMLResponse("<h1>itsuki.html not found</h1>", status_code=404)


@app.get("/Selections/{filename}")
async def serve_selections_file(filename: str):
    for base in [os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "Itsuki_ai")]:
        fpath = os.path.join(base, "Selections", filename)
        if os.path.exists(fpath):
            return FileResponse(fpath)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/itsuki.jpg")
async def get_itsuki_pfp():
    for base in [os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "Itsuki_ai")]:
        pfp_path = os.path.join(base, "Pfp", "itsuki.jpg")
        if os.path.exists(pfp_path):
            return FileResponse(pfp_path)
    raise HTTPException(status_code=404, detail="Image not found")


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")

    conversation_history.append({"role": "user", "content": user_text})

    try:
        response = groq_client.chat.completions.create(
            messages=conversation_history,
            model="openai/gpt-oss-120b",
            max_tokens=250,
        )

        teks_jawaban_raw = response.choices[0].message.content.strip()
        conversation_history.append(
            {"role": "assistant", "content": teks_jawaban_raw}
        )

        # Parse Emotion Tag & Clean Text
        ekspresi = "idle"
        teks_bersih = teks_jawaban_raw

        if teks_jawaban_raw.startswith("[") and "]" in teks_jawaban_raw:
            end_idx = teks_jawaban_raw.index("]")
            ekspresi = teks_jawaban_raw[1:end_idx].lower()
            teks_bersih = teks_jawaban_raw[end_idx + 1 :].strip()

        # Clean repetitive dots that trigger echo artifacts in TTS
        teks_bersih = teks_bersih.replace("...", ".").replace("..", ".")

        # Request Voice from Fish Audio API
        audio_b64 = None
        try:
            url = "https://api.fish.audio/v1/tts"
            headers = {
                "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
                "Content-Type": "application/json",
                "model": "s2.1-pro-free",
            }
            payload = {
                "text": teks_bersih,
                "reference_id": "8c603f53ffd04b0c966e1561d252b75a",
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
        if conversation_history and conversation_history[-1]["role"] == "user":
            conversation_history.pop()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset_endpoint():
    global conversation_history
    conversation_history = [SYSTEM_PROMPT]
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
