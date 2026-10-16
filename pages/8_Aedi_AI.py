import os
import streamlit as st
from google import genai
from google.genai import types

st.title("🤖 Project AI Assistant")
st.caption("Powered by Gemini and Streamlit")

MODEL_CANDIDATES = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-3.8-flash",
]

SYSTEM_PROMPT = (
    "You are a helpful assistant for building and plot planning. "
    "If the user has uploaded a plan, read it carefully and base your answers on it. "
    "If something is not clearly visible in the plan, say so instead of guessing."
)


def find_api_key():
    """Look for a key: pasted in this session, then secrets.toml, then an environment variable."""
    key = st.session_state.get("user_api_key")
    if key:
        return key
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key:
            return key
    except Exception:
        pass  # no secrets file in a packaged app
    return os.environ.get("GEMINI_API_KEY", "")


@st.cache_resource
def get_ai_client(api_key):
    # timeout in milliseconds: 60 seconds, since plans take longer to read
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60000),
    )


api_key = find_api_key()
if not api_key:
    st.info(
        "Aedi AI needs a free Google Gemini API key. Get one at "
        "https://aistudio.google.com/apikey, then paste it below. "
        "The key is kept only while this app is open and is never saved to disk."
    )
    entered = st.text_input("Gemini API key", type="password")
    if entered.strip():
        st.session_state["user_api_key"] = entered.strip()
        st.rerun()
    st.stop()

client = get_ai_client(api_key)

if st.session_state.get("user_api_key"):
    if st.button("Change API key"):
        st.session_state.pop("user_api_key", None)
        st.rerun()

# ---------- Plan upload ----------
uploaded_plan = st.file_uploader(
    "Upload your plan (PNG, JPG or PDF, under 10 MB)",
    type=["png", "jpg", "jpeg", "pdf"],
)

if uploaded_plan is not None:
    st.session_state.plan_bytes = uploaded_plan.getvalue()
    st.session_state.plan_mime = uploaded_plan.type or "application/pdf"
    st.session_state.plan_name = uploaded_plan.name
else:
    st.session_state.pop("plan_bytes", None)

if "plan_bytes" in st.session_state:
    st.success(f"Plan loaded: {st.session_state.plan_name}")
    if st.session_state.plan_mime.startswith("image/"):
        st.image(st.session_state.plan_bytes, caption="Your plan", width="stretch")


def generate_reply(history, prompt, placeholder):
    last_error = RuntimeError("No model responded.")
    for model in MODEL_CANDIDATES:
        try:
            chat = client.chats.create(
                model=model,
                history=history,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            reply = ""
            for chunk in chat.send_message_stream(prompt):
                reply += chunk.text or ""
                placeholder.markdown(reply + "▌")
            if reply:
                placeholder.markdown(reply)
                return reply
            last_error = RuntimeError("The model returned an empty reply.")
        except Exception as error:
            last_error = error
            placeholder.markdown("Switching to another model...")
    raise last_error


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_prompt = st.chat_input("Ask a question about your plan or project...")

if user_prompt:
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})

    api_formatted_history = []

    # The uploaded plan goes first so the model can refer to it in every answer.
    if "plan_bytes" in st.session_state:
        api_formatted_history.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        data=st.session_state.plan_bytes,
                        mime_type=st.session_state.plan_mime,
                    ),
                    types.Part.from_text(text="This is my plan. Use it to answer my questions."),
                ],
            )
        )
        api_formatted_history.append(
            types.Content(
                role="model",
                parts=[types.Part.from_text(text="Understood. I have your plan. What would you like to know?")],
            )
        )

    for msg in st.session_state.chat_history[:-1]:
        role_mapping = "user" if msg["role"] == "user" else "model"
        api_formatted_history.append(
            types.Content(
                role=role_mapping,
                parts=[types.Part.from_text(text=msg["content"])],
            )
        )

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            reply = generate_reply(api_formatted_history, user_prompt, placeholder)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
        except Exception as error:
            placeholder.empty()
            st.error(f"Could not get a reply. Please try again in a minute. Details: {error}")
            st.session_state.chat_history.pop()