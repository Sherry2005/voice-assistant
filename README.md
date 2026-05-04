# 🇩🇪 Deutsch Üben — German Speaking Practice Assistant

A real-time AI-powered German language tutor: speak German, get corrected, and hear native-quality responses.

Built on a three-stage voice pipeline: **Whisper STT → Llama 3.3 LLM → Microsoft Edge Neural TTS**

---

## Stack

| Layer | Technology |
|---|---|
| Speech-to-Text | Groq Whisper large-v3 (German-optimized) |
| LLM | Groq Llama 3.3 70B Versatile |
| Text-to-Speech | Microsoft Edge Neural TTS (edge-tts) |
| UI | Streamlit |

---

## Features

- 🎤 **In-browser voice recording** — no extra packages needed
- 🇩🇪 **Three learning levels** — A1/A2 Beginner · B1/B2 Intermediate · C1 Advanced
- ✏️ **Inline grammar correction** — tutor corrects up to 1–2 mistakes per turn, without interrupting the conversation flow
- 🔊 **Six German neural voices** — Katja, Conrad, Amala, Bernd, Elke, Killian (all de-DE)
- 🎚️ **Adjustable speaking speed** — 0.7× (learner-friendly) to 1.2× (native pace)
- 🧠 **Multi-turn memory** — last 10 exchanges kept in context
- 🔐 **API key via Streamlit secrets** — safe for deployment

---

## How it works

1. **Speak** into the browser mic in German (or try in German — the tutor will help)
2. **Whisper** transcribes your audio with a German language hint for higher accuracy
3. **Llama 3.3** generates a level-appropriate response with corrections if needed
4. **Edge TTS** synthesizes the reply in a natural German neural voice and autoplays it

---

## Setup

```bash
pip install streamlit groq edge-tts
```

Add your Groq API key to `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_..."
```

Then run:

```bash
streamlit run app.py
```

---

## Live Demo

[Deployed on Streamlit Cloud]([https://your-app-url.streamlit.app](https://voice-assistant-ai-german.streamlit.app/))

---

## Author

**Sherry Mohareb** — AI Engineer  
[GitHub](https://github.com/Sherry2005) · [LinkedIn](https://linkedin.com/in/sherry-mohareb)
