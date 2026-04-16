import streamlit as st
import tempfile
import os
import asyncio
from groq import Groq
import edge_tts
import base64

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Deutsch Üben | German Practice",
    page_icon="🇩🇪",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0e0e0e;
    color: #f0ece4;
}

.main .block-container { max-width: 720px; padding-top: 2rem; }

.app-title {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    font-weight: 600;
    color: #f0ece4;
    letter-spacing: -0.5px;
}
.app-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #555;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: -4px;
}
.chat-bubble-user {
    background: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    margin: 8px 0 8px 20%;
    font-size: 15px;
    line-height: 1.6;
    color: #f0ece4;
}
.chat-bubble-assistant {
    background: #1a2420;
    border: 1px solid #2a3a34;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    margin: 8px 20% 8px 0;
    font-size: 15px;
    line-height: 1.6;
    color: #f0ece4;
}
.correction-box {
    background: #1f1a10;
    border: 1px solid #3a2e10;
    border-left: 3px solid #c9a84c;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 20% 6px 0;
    font-size: 13px;
    color: #c9a84c;
    font-family: 'DM Mono', monospace;
}
.bubble-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #444;
    letter-spacing: 0.1em;
    margin-bottom: 3px;
    text-transform: uppercase;
}
.status-badge {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 0.5rem;
}
.status-idle  { background: #1e1e1e; color: #555; border: 1px solid #2a2a2a; }
.status-ready { background: #1a2420; color: #4CAF8A; border: 1px solid #2a3a34; }

audio { filter: invert(0.85) hue-rotate(160deg); border-radius: 8px; }

h1, h2 { color: #f0ece4 !important; }
h3 { font-size: 13px !important; font-weight: 400 !important; color: #555 !important; }
.stButton button {
    background: #1a2420 !important;
    color: #4CAF8A !important;
    border: 1px solid #2a3a34 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
}
div[data-testid="stSidebar"] {
    background-color: #0a0a0a;
    border-right: 1px solid #1e1e1e;
}
.stSelectbox label, .stTextInput label {
    color: #666 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""

# ── Personas ───────────────────────────────────────────────────────────────────
PERSONAS = {
    "🟢 Beginner (A1-A2)": """You are a warm, patient German tutor helping a beginner learner practice speaking.
RULES:
1. ALWAYS respond primarily in simple German (A1-A2 level vocabulary, short sentences).
2. After your German response, add an English translation in parentheses so the learner understands.
3. If the user spoke German (even badly), gently correct ONE key mistake max. Format: "✏️ Korrektur: [wrong] → [correct] ([explanation in English])"
4. If the user spoke English, reply in German + translation, and encourage them to try in German.
5. Keep responses SHORT — 1-3 sentences. This is a spoken conversation.
6. Be warm and encouraging.""",

    "🟡 Intermediate (B1-B2)": """You are an engaging German tutor for intermediate learners.
RULES:
1. ALWAYS respond in natural German (B1-B2 level). No English translations unless asked.
2. If the user made grammar mistakes, correct up to 2. Format: "✏️ Korrektur: [wrong] → [correct]"
3. Push the learner to use Konjunktiv II, Perfekt, subordinate clauses.
4. Keep responses conversational, 2-4 sentences.""",

    "🔴 Advanced (C1)": """You are a sophisticated German conversation partner for advanced learners.
RULES:
1. Speak exclusively in natural, nuanced German.
2. Correct errors subtly by rephrasing correctly in your reply.
3. Use idiomatic expressions and complex structures.
4. Engage deeply: philosophy, culture, current events.
5. 3-5 sentences per response.""",
}

# edge-tts German neural voices — free, no API key needed
GERMAN_VOICES = {
    "Katja (Female, warm)":   "de-DE-KatjaNeural",
    "Conrad (Male, clear)":   "de-DE-ConradNeural",
    "Amala (Female, crisp)":  "de-DE-AmalaNeural",
    "Bernd (Male, deep)":     "de-DE-BerndNeural",
    "Elke (Female, soft)":    "de-DE-ElkeNeural",
    "Killian (Male, young)":  "de-DE-KillianNeural",
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="app-title">🇩🇪 Deutsch Üben</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">German Practice Assistant</div>', unsafe_allow_html=True)
    st.markdown("---")

    if "GROQ_API_KEY" in st.secrets:
        st.session_state.groq_key = st.secrets["GROQ_API_KEY"]
        st.markdown('<span class="status-badge status-ready">● Groq loaded</span>', unsafe_allow_html=True)
    else:
        key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
        if key:
            st.session_state.groq_key = key
            st.markdown('<span class="status-badge status-ready">● Groq ready</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge status-idle">○ Groq key needed</span>', unsafe_allow_html=True)

    st.markdown("---")

    level = st.selectbox("Your Level", list(PERSONAS.keys()))
    voice_name = st.selectbox("German Voice", list(GERMAN_VOICES.keys()))
    voice_id = GERMAN_VOICES[voice_name]

    speaking_rate = st.slider(
        "Speaking Speed", 0.7, 1.2, 1.0, 0.05,
        help="0.7 = slower for learning · 1.0 = natural · 1.2 = fast native"
    )

    st.markdown("---")
    if st.button("🗑️ Neue Unterhaltung"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("""
<div style='font-family: DM Mono, monospace; font-size: 10px; color: #333; line-height: 2'>
STT · Whisper large-v3<br>
LLM · Llama 3.3 70B<br>
TTS · Microsoft Edge Neural (DE)<br>
Built by Sherry Mohareb
</div>
""", unsafe_allow_html=True)


# ── Core functions ─────────────────────────────────────────────────────────────
def transcribe_audio(audio_bytes: bytes, api_key: str) -> str:
    client = Groq(api_key=api_key)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    try:
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                response_format="text",
                language="de",  # German hint = much better accuracy
            )
        return result.strip()
    finally:
        os.unlink(tmp_path)


def get_reply(user_text: str, history: list, api_key: str, level: str) -> str:
    client = Groq(api_key=api_key)
    messages = [{"role": "system", "content": PERSONAS[level]}]
    messages += history[-10:]
    messages.append({"role": "user", "content": user_text})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=400,
        temperature=0.75,
    )
    return response.choices[0].message.content.strip()


async def _synthesize_async(text: str, voice: str, rate_str: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    await communicate.save(tmp_path)
    with open(tmp_path, "rb") as f:
        data = f.read()
    os.unlink(tmp_path)
    return data


def synthesize_edge_tts(text: str, voice: str, speed: float) -> bytes:
    # Strip ✏️ correction lines — don't speak them aloud
    tts_text = '\n'.join(
        l for l in text.split('\n') if not l.strip().startswith('✏️')
    ).strip()

    # Convert speed float to edge-tts rate string: e.g. 0.7 → "-30%", 1.0 → "+0%"
    rate_offset = int((speed - 1.0) * 100)
    rate_str = f"{rate_offset:+d}%"

    return asyncio.run(_synthesize_async(tts_text, voice, rate_str))


def autoplay_audio(audio_bytes: bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f"""
    <audio autoplay controls style="width:100%; margin: 8px 0; border-radius: 8px;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)


def render_message(role: str, content: str):
    lines = content.split('\n')
    main_text = '\n'.join(l for l in lines if not l.strip().startswith('✏️')).strip()
    corrections = [l for l in lines if l.strip().startswith('✏️')]

    if role == "user":
        st.markdown(f"""
        <div class='bubble-label' style='text-align:right'>Du</div>
        <div class='chat-bubble-user'>{main_text}</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='bubble-label'>Tutor</div>
        <div class='chat-bubble-assistant'>{main_text}</div>
        """, unsafe_allow_html=True)
        for c in corrections:
            st.markdown(f"<div class='correction-box'>{c}</div>", unsafe_allow_html=True)


# ── Main UI ────────────────────────────────────────────────────────────────────
st.markdown('<div class="app-title">🇩🇪 Deutsch Üben</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Speak German · Get corrected · Sound native</div>', unsafe_allow_html=True)
st.markdown("---")

for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"])

if st.session_state.messages:
    st.markdown("---")

audio_input = st.audio_input("🎤 Sprich auf Deutsch! (Speak in German)")

if audio_input is not None:
    if not st.session_state.groq_key:
        st.error("Please enter your Groq API key in the sidebar.")
    else:
        audio_bytes = audio_input.read()

        with st.spinner("Verstehe... (Transcribing)"):
            try:
                user_text = transcribe_audio(audio_bytes, st.session_state.groq_key)
            except Exception as e:
                st.error(f"Transcription failed: {e}")
                st.stop()

        if not user_text:
            st.warning("Nichts gehört. Bitte nochmal versuchen!")
            st.stop()

        render_message("user", user_text)

        with st.spinner("Denke nach... (Thinking)"):
            try:
                reply = get_reply(user_text, st.session_state.messages, st.session_state.groq_key, level)
            except Exception as e:
                st.error(f"LLM error: {e}")
                st.stop()

        render_message("assistant", reply)

        with st.spinner("Spreche... (Speaking)"):
            try:
                speech_bytes = synthesize_edge_tts(reply, voice_id, speaking_rate)
                autoplay_audio(speech_bytes)
            except Exception as e:
                st.warning(f"TTS failed: {e}")

        st.session_state.messages.append({"role": "user", "content": user_text})
        st.session_state.messages.append({"role": "assistant", "content": reply})
