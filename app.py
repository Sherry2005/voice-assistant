import streamlit as st
import tempfile
import os
from groq import Groq
from gtts import gTTS
import base64

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Voice Assistant",
    page_icon="🎙️",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.main .block-container { max-width: 720px; padding-top: 2rem; }

.chat-bubble-user {
    background: #f0f0f0;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    margin: 8px 0 8px 20%;
    font-size: 15px;
    line-height: 1.6;
    color: #1a1a1a;
}
.chat-bubble-assistant {
    background: #e8f5ee;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    margin: 8px 20% 8px 0;
    font-size: 15px;
    line-height: 1.6;
    color: #1a1a1a;
}
.bubble-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #888;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
}
.status-badge {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 1rem;
}
.status-idle    { background: #f0f0f0; color: #666; }
.status-ready   { background: #e8f5ee; color: #1D9E75; }
.status-error   { background: #fde8e8; color: #c0392b; }

h1 { font-size: 22px !important; font-weight: 500 !important; }
h3 { font-size: 14px !important; font-weight: 500 !important; color: #888 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎙️ voice assistant")
    st.markdown("---")

    # API key — check secrets first, fallback to input
    if "GROQ_API_KEY" in st.secrets:
        st.session_state.api_key = st.secrets["GROQ_API_KEY"]
        st.markdown('<span class="status-badge status-ready">● API key loaded</span>', unsafe_allow_html=True)
    else:
        key_input = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
        if key_input:
            st.session_state.api_key = key_input
            st.markdown('<span class="status-badge status-ready">● key saved</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge status-idle">○ no key set</span>', unsafe_allow_html=True)

    st.markdown("---")

    persona = st.selectbox("Persona", [
        "Helpful Assistant",
        "Concise & Direct",
        "Technical Expert",
        "Creative & Witty",
    ])

    lang = st.selectbox("TTS Language", [
        ("English", "en"),
        ("Arabic", "ar"),
        ("French", "fr"),
        ("Spanish", "es"),
        ("German", "de"),
    ], format_func=lambda x: x[0])

    tts_slow = st.checkbox("Slow speech", value=False)

    st.markdown("---")
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("""
<div style='font-family: DM Mono, monospace; font-size: 11px; color: #aaa; line-height: 1.8'>
STT · Whisper large-v3<br>
LLM · Llama 3.3 70B<br>
TTS · gTTS<br>
Built by Sherry Mohareb
</div>
""", unsafe_allow_html=True)

# ── Persona system prompts ─────────────────────────────────────────────────────
PERSONAS = {
    "Helpful Assistant": "You are a helpful, friendly voice assistant. Keep answers clear and conversational — typically 2-4 sentences. Avoid bullet points; speak in natural flowing sentences.",
    "Concise & Direct": "You are a concise voice assistant. Answer in 1-2 sentences maximum. Be direct and precise. No filler words.",
    "Technical Expert": "You are a technical expert. Give precise, accurate technical answers using proper terminology. Explain clearly but don't oversimplify.",
    "Creative & Witty": "You are a creative, witty assistant. Be imaginative and engaging. Use vivid language and unexpected angles in your answers.",
}

# ── Helper: transcribe audio ───────────────────────────────────────────────────
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
            )
        return result.strip()
    finally:
        os.unlink(tmp_path)


# ── Helper: get LLM reply ──────────────────────────────────────────────────────
def get_reply(user_text: str, history: list, api_key: str, persona: str) -> str:
    client = Groq(api_key=api_key)
    system_prompt = PERSONAS[persona]
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# ── Helper: text → audio bytes ─────────────────────────────────────────────────
def synthesize_speech(text: str, lang_code: str, slow: bool) -> bytes:
    tts = gTTS(text=text, lang=lang_code, slow=slow)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tts.save(f.name)
        tmp_path = f.name
    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()
    os.unlink(tmp_path)
    return audio_bytes


# ── Helper: autoplay audio ─────────────────────────────────────────────────────
def autoplay_audio(audio_bytes: bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f"""
    <audio autoplay style="width:100%; margin: 8px 0;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)


# ── Main UI ────────────────────────────────────────────────────────────────────
st.markdown("## 🎙️ voice assistant")
st.markdown("### record your voice — get a spoken reply")

st.markdown("---")

# Render conversation history
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    if role == "user":
        st.markdown(f"""
        <div class='bubble-label' style='text-align:right'>YOU</div>
        <div class='chat-bubble-user'>{content}</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='bubble-label'>ASSISTANT</div>
        <div class='chat-bubble-assistant'>{content}</div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── Audio input ────────────────────────────────────────────────────────────────
audio_input = st.audio_input("🎤 Record your message")

if audio_input is not None:
    if not st.session_state.api_key:
        st.error("Please enter your Groq API key in the sidebar.")
    else:
        audio_bytes = audio_input.read()

        # Step 1: Transcribe
        with st.spinner("Transcribing..."):
            try:
                user_text = transcribe_audio(audio_bytes, st.session_state.api_key)
            except Exception as e:
                st.error(f"Transcription failed: {e}")
                st.stop()

        if not user_text:
            st.warning("Couldn't detect any speech. Try again.")
            st.stop()

        # Show user bubble immediately
        st.markdown(f"""
        <div class='bubble-label' style='text-align:right'>YOU</div>
        <div class='chat-bubble-user'>{user_text}</div>
        """, unsafe_allow_html=True)

        # Step 2: LLM reply
        with st.spinner("Thinking..."):
            try:
                reply = get_reply(
                    user_text,
                    st.session_state.messages,
                    st.session_state.api_key,
                    persona,
                )
            except Exception as e:
                st.error(f"LLM error: {e}")
                st.stop()

        # Show assistant bubble
        st.markdown(f"""
        <div class='bubble-label'>ASSISTANT</div>
        <div class='chat-bubble-assistant'>{reply}</div>
        """, unsafe_allow_html=True)

        # Step 3: TTS
        with st.spinner("Speaking..."):
            try:
                lang_code = lang[1]
                speech_bytes = synthesize_speech(reply, lang_code, tts_slow)
                autoplay_audio(speech_bytes)
            except Exception as e:
                st.warning(f"TTS failed (reply still shown above): {e}")

        # Save to history
        st.session_state.messages.append({"role": "user", "content": user_text})
        st.session_state.messages.append({"role": "assistant", "content": reply})
