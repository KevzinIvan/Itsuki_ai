import os
import sys
import time
import requests
from groq import Groq

try:
    import pygame
except ImportError:
    pygame = None

from app import app


# 1. API Keys Configuration
GROQ_API_KEY = "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"
FISH_AUDIO_API_KEY = "sk-fish-nRVYZqD0nZSKThs8gxt4rDZNh1T6gjN2Z6L379x_YDc"

groq_client = Groq(api_key=GROQ_API_KEY)


def main():
  # Strict System Prompt agar tidak bernyanyi, tidak OOC, dan wajib menyertakan tag emosi
  conversation_history = [{
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
  }]

  pygame.mixer.init()
  os.system("cls" if os.name == "nt" else "clear")

  print("==================================================")
  print("          ITSUKI NAKANO Made by Gweh              ")
  print("==================================================")
  print("Ketik 'exit' atau 'quit' untuk keluar dari obrolan.\n")

  while True:
    try:
      user_input = input("Kamu: ").strip()

      if user_input.lower() in ["exit", "quit", "keluar"]:
        print("\nItsuki: Goodbye! Have a nice day!")
        break

      if not user_input:
        continue

      conversation_history.append({"role": "user", "content": user_input})
      print("Itsuki sedang berpikir...")

      response = groq_client.chat.completions.create(
          messages=conversation_history,
          model="openai/gpt-oss-120b",
          max_tokens=250,
      )

      teks_jawaban_raw = response.choices[0].message.content.strip()
      conversation_history.append(
          {"role": "assistant", "content": teks_jawaban_raw}
      )

      # 2. Parsing Emotion Tag & Pembersihan Teks
      ekspresi = "idle"
      teks_bersih = teks_jawaban_raw

      if teks_jawaban_raw.startswith("[") and "]" in teks_jawaban_raw:
        end_idx = teks_jawaban_raw.index("]")
        ekspresi = teks_jawaban_raw[1:end_idx].lower()
        teks_bersih = teks_jawaban_raw[end_idx + 1 :].strip()

      # Pembersihan tanda baca berulang yang sering memicu gema/artefak di TTS
      teks_bersih = teks_bersih.replace("...", ".").replace("..", ".")

      # Tampilkan ekspresi & teks bersih di terminal
      print(f"\nItsuki [{ekspresi}]: {teks_bersih}\n")
      sys.stdout.flush()

      # 3. Request Suara ke Fish Audio dengan Parameter Redam Gema
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
          "temperature": 0.7,  # Menjaga kestabilan variasi suara
          "top_p": 0.7,  # Menekan potensi artefak/gema
      }

      res_tts = requests.post(url, headers=headers, json=payload, timeout=30)

      if res_tts.status_code == 200:
        filename = "suara_itsuki.mp3"
        with open(filename, "wb") as f:
          f.write(res_tts.content)

        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
          time.sleep(0.1)

        pygame.mixer.music.unload()
      else:
        print(f"(Gagal memuat suara: Status {res_tts.status_code})")

    except KeyboardInterrupt:
      print("\n\nObrolan dihentikan. Sampai jumpa!")
      break
    except Exception as e:
      print(f"\nTerjadi kesalahan: {e}")


if __name__ == "__main__":
  main()