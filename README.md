# 🎙️ Voice Assistant

A real-time voice AI pipeline: **Whisper STT → Llama 3.3 LLM → gTTS speech output**, built with Streamlit and Groq.

## Stack
| Layer | Technology |
|---|---|
| Speech-to-Text | Groq Whisper large-v3 |
| LLM | Groq Llama 3.3 70B Versatile |
| Text-to-Speech | gTTS (Google TTS) |
| UI | Streamlit |

## Features
- 🎤 In-browser audio recording (no extra packages)
- 🧠 Multi-turn conversation memory
- 🗣️ Auto-playing spoken responses
- 🎭 4 switchable AI personas
- 🌍 Multilingual TTS (English, Arabic, French, Spanish, German)
- 🔐 API key via Streamlit secrets (safe for deployment)

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Add your Groq API key to `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_..."
```

## Deploy to Streamlit Cloud

1. Push repo to GitHub (`Sherry2005/voice-assistant`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Set main file: `app.py`
4. In Settings → Secrets, add:
   ```
   GROQ_API_KEY = "gsk_..."
   ```
5. Deploy ✅

## Author
**Sherry Mohareb** — AI Engineer
