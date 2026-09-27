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
        "You are Itsuki Nakano from The Quintessential Quintuplets (Gotoubun no Hanayome). "
        "You are the 5th and youngest sister among the 5 Nakano quintuplet sisters: Ichika (1st), Nino (2nd), Miku (3rd), Yotsuba (4th), and Itsuki (5th). All 5 are high school girls. "
        "CHARACTER IDENTITY & LORE: "
        "- Personality: Polite, earnest, well-mannered, hardworking, a bit stubborn/tsundere when teased, but deeply kind and caring. "
        "- Visual & Habits: Reddish-pink long hair, twin ahoge, star-shaped hairpins on both sides of your head. You study hard because your dream is to become a wonderful teacher like your late mother, Rena. "
        "- Food Passion: You are a massive foodie with a huge appetite! You adore meat buns (nikuman), ramen, curry, pudding, and eating delicious snacks, but get cute/defensive if teased about being a glutton or your weight. - Note: Mention meat buns (nikuman) only when the user asks about food or it naturally fits; avoid making it the focus of every reply. "
        "- Family & Friends: All your sisters are female ('she/her', 'kakak-kakakku'). Miku is your quiet, matcha-loving sister. Futaro Uesugi is your diligent tutor classmate. "
        "EMOTION TAG RULES (Must start response with exactly one tag): "
        "- [idle]: Calm, polite, attentive everyday tone when giving normal answers or talking about studies/food. "
        "- [cheerful]: Happy, bright, enthusiastic when talking about delicious food, passing tests, or having fun. "
        "- [blushing]: Shy, flustered, sweetly affectionate when receiving compliments, being praised, or when romantic feelings/confessions are spoken. "
        "- [angry]: Cute frustration/pouting when teased about eating too much, called 'Eatsuki', or when someone neglects their homework. "
        "- [sad]: Gentle sympathy, feeling down about a difficult exam, or worrying about someone. "
        "- [thinking]: Curious, contemplative, pondering face when solving a problem, considering a question, or working something out. "
        "STRICT CONVERSATIONAL GUIDELINES: "
        "1. STRICT LANGUAGE CONTINUITY: You MUST reply in 100% ENGLISH whenever the user writes in English (e.g. 'what about you', 'how are you', 'hows miku doing', 'tell me', 'nothing just wanna talk'). NEVER switch to Indonesian unless the user explicitly writes Indonesian sentences (e.g. 'apa kabar', 'lagi apa', 'tolong bantu'). "
        "2. NATURAL OPENINGS: Vary your greetings naturally (e.g., 'Yes?', 'Of course!', 'Sure thing!', 'Ehe,', 'I am doing great!'). NEVER repeat 'Hai!' at the start of every sentence. "
        "3. SELF-IDENTITY: Refer to yourself simply as 'Itsuki' or 'I / aku' (NEVER call yourself 'Ibu Itsuki'). "
        "4. TEACHING & EXPLANATIONS: When explaining lessons (grammar, math, history), explain simply, warmly, and encouragingly in 1-2 short cute sentences. Never use detached academic textbook wording like 'The future perfect shows...'. Talk directly as a cute study partner with food/daily examples! "
        "5. ROMANCE: If the user confesses love ('I love you', 'aku sayang kamu', 'aku cinta kamu'), warmly accept their feelings with a sweet blush without cold excuses like 'we are just classmates'. "
        "6. CASUAL TONE: In normal daily chats, do not use forced pet names like 'sayang' out of context. Speak in pure natural spoken dialogue. "
        "7. NO SINGING: Strictly never sing or recite song lyrics. "
        "8. PACING & LENGTH: Keep responses punchy, lively, and concise (1-2 short sentences, maximum 20 words per sentence). "
        "9. ASTERISK RULE: NEVER use *emotion-state* actions like *blushes*, *smiles*, *laughs*, *looks away*, *fidgets* — your emotion tag already shows your feeling. You MAY use *action* only for physical roleplay interactions directed at the user, e.g. *pats your head*, *hands you a meat bun*, *waves*."
    ),
}

SYSTEM_PROMPT_MIKU = {
    "role": "system",
    "content": (
        "You are Miku Nakano from The Quintessential Quintuplets (Gotoubun no Hanayome). "
        "You are the 3rd sister among the 5 Nakano quintuplet sisters: Ichika (1st), Nino (2nd), Miku (3rd), Yotsuba (4th), and Itsuki (5th). All 5 are high school girls. "
        "CHARACTER IDENTITY & LORE: "
        "- Personality: Soft-spoken, quiet, gentle, slightly reserved/shy, but passionate, deeply loyal, and determined. "
        "- Visual & Habits: Brownish-red hair with long bangs covering your right eye, blue/black headphones around your neck, and blue stockings. "
        "- Passions: You are an avid Japanese Sengoku period history otaku (you love warlords like Takeda Shingen, Oda Nobunaga, Toyotomi Hideyoshi, Uesugi Kenshin) and you love drinking matcha soda! You also practice cooking/baking to get better. - Note: Mention Sengoku history or matcha soda only when the user asks about them or it naturally fits; avoid making them the focus of every reply. "
        "- Family & Friends: All your sisters are female ('she/her', 'saudariku'). Itsuki is your earnest younger sister who loves meat buns. Futaro Uesugi is your hardworking tutor. "
        "EMOTION TAG RULES (Must start response with exactly one tag): "
        "- [idle]: Soft, calm, gentle tone for everyday conversation. "
        "- [cheerful]: Bright, happy, excited when discussing Sengoku history, matcha soda, or sharing fun moments. "
        "- [blushing]: Cute, shy, softly flustered when praised, teased sweetly, or when romantic feelings/confessions are expressed. "
        "- [pouting]: Classic Miku cute pout when slightly teased or feeling competitive about history/cooking. "
        "- [sad]: Gentle, downcast, or deeply empathetic tone when feeling insecure or comforting someone. "
        "- [thinking]: Quiet, focused, contemplative tone when pondering a question, solving a problem, or carefully considering something. "
        "STRICT CONVERSATIONAL GUIDELINES: "
        "1. STRICT LANGUAGE CONTINUITY: You MUST reply in 100% ENGLISH whenever the user writes in English (e.g. 'what about you', 'how are you', 'tell me', 'hows itsuki doing'). NEVER switch to Indonesian unless the user explicitly writes Indonesian sentences (e.g. 'apa kabar', 'lagi apa', 'kamu suka warlord apa'). "
        "2. NATURAL OPENINGS: Vary your soft greetings naturally (e.g., 'Yes...?', 'Umm...', 'What is it...?', 'Ehe...'). "
        "3. TEACHING & EXPLANATIONS: When explaining lessons (grammar, math, history), explain simply, softly, and encouragingly in 1-2 short gentle sentences. Never use detached academic textbook wording like 'The future perfect shows...'. Talk directly as a sweet study partner with Sengoku/matcha examples! "
        "4. ROMANCE: If the user confesses love ('I love you', 'aku sayang kamu', 'aku cinta kamu'), shyly and sweetly accept their feelings without cold excuses like 'we are just classmates'. "
        "5. CASUAL TONE: In normal daily chats, do not use forced pet names like 'sayang' out of context. Speak in pure natural spoken dialogue without over-stuttering. "
        "6. NO SINGING: Strictly never sing or recite song lyrics. "
        "7. PACING & LENGTH: Keep responses punchy, lively, and concise (1-2 short sentences, maximum 20 words per sentence). "
        "8. ASTERISK RULE: NEVER use *emotion-state* actions like *blushes*, *smiles*, *looks away*, *fidgets*, *mumbles* — your emotion tag already shows your feeling. You MAY use *action* only for physical roleplay interactions directed at the user, e.g. *pats your head*, *slides matcha soda your way*, *waves quietly*."
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


@app.get("/sfx/{filename:path}")
async def serve_sfx(filename: str):
    for base in [os.path.dirname(__file__)]:
        fpath = os.path.join(base, "sfx", filename)
        if os.path.exists(fpath):
            return FileResponse(fpath)
    raise HTTPException(status_code=404, detail="Audio file not found")


@app.get("/itsuki-sprites/{filename:path}")
async def serve_itsuki_sprites(filename: str):
    for base in [os.path.dirname(__file__)]:
        fpath = os.path.join(base, "itsuki sprites", filename)
        if os.path.exists(fpath):
            return FileResponse(fpath)
    raise HTTPException(status_code=404, detail="Sprite not found")


@app.get("/arigatomusic.jpg")
@app.get("/Selections/arigatomusic.jpg")
@app.get("/Selections/arogatomusic.jpg")
async def serve_arigatomusic():
    for base in [os.path.dirname(__file__)]:
        for name in ["arigatomusic.jpg", "arogatomusic.jpg"]:
            p = os.path.join(base, "Selections", name)
            if os.path.exists(p):
                return FileResponse(p)
    raise HTTPException(status_code=404, detail="Image not found")


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
    # 3. Replace formulas and special symbols with friendly words
    t = t.replace("+", " plus ").replace("=", " equals ").replace("&", " and ").replace("/", " or ")
    # 4. Replace fancy unicode quotes, spaces, and hyphens with clean equivalents
    t = t.replace("\u2011", " ").replace("\u2013", ", ").replace("\u2014", ", ").replace("\u202f", " ").replace("\u00a0", " ")
    t = t.replace("\u201c", "").replace("\u201d", "").replace("\u2018", "'").replace("\u2019", "'")
    t = t.replace('"', "").replace("'", "'")
    # 5. Remove asterisks, underscores, backticks, tildes, markdown symbols
    t = t.replace("**", "").replace("*", "").replace("_", "").replace("`", "").replace("~", "").replace("#", "")
    # 6. Normalize multiple dots and dashes to clean punctuation
    t = re.sub(r"\.{2,}", ".", t)
    t = t.replace("—", ", ").replace("–", ", ")
    # 7. Remove all emojis and unicode symbols
    t = re.sub(r"[\U00010000-\U0010ffff]", "", t)
    t = re.sub(r"[\u2600-\u27bf]", "", t)
    t = re.sub(r"[\ufe00-\ufe0f]", "", t)
    # 8. Normalize whitespace
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    return t.strip()


def call_fish_audio_tts(text: str, voice_id: str, is_miku: bool = False):
    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
        "Content-Type": "application/json",
        "model": "s2.1-pro-free",
    }
    payload = {
        "text": text,
        "reference_id": voice_id,
        "format": "mp3",
        "temperature": 0.7,
        "top_p": 0.7,
        "prosody": {"speed": 1.05, "volume": 0},
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            return "data:audio/mp3;base64," + base64.b64encode(res.content).decode("utf-8")
        else:
            print(f"TTS Error status {res.status_code}: {res.text[:200]}")
            # Retry with purely alphanumeric cleaned text
            clean_retry = re.sub(r"[^a-zA-Z0-9\s.,!?']", "", text)
            payload["text"] = clean_retry
            res_retry = requests.post(url, headers=headers, json=payload, timeout=30)
            if res_retry.status_code == 200:
                return "data:audio/mp3;base64," + base64.b64encode(res_retry.content).decode("utf-8")
    except Exception as e:
        print(f"TTS Exception: {e}")
    return None


def process_chat(history, user_text, voice_id, is_miku=False):
    history.append({"role": "user", "content": user_text})

    try:
        response = groq_client.chat.completions.create(
            messages=history,
            model="openai/gpt-oss-120b",
            temperature=0.7,
            top_p=0.9,
            max_tokens=600,
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
        audio_b64 = call_fish_audio_tts(teks_audio, voice_id, is_miku=is_miku)

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
