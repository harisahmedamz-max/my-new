import streamlit as st
from openai import OpenAI

# 🔑 Init OpenAI client
client = OpenAI()

# 👉 Replace with your correct Assistant ID from Playground
ASSISTANT_ID = "asst_PogREgRWsM0PHH6LqvV114YR"

st.title("💬 Plaid-Libs")

# Initialize session state
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []  # Chat history

# Chat input
user_input = st.chat_input("Type your message...")

if user_input:
    # Save user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Send user message to thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input,
    )

    # Run assistant with the correct ID
    run = client.beta.threads.runs.create_and_poll(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    # Get latest messages from the thread
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)

    # Find assistant’s last reply
    for m in reversed(messages.data):
        if m.role == "assistant":
            reply = m.content[0].text.value
            st.session_state.messages.append({"role": "assistant", "content": reply})
            break

# Display conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Debug info (optional)
if st.checkbox("🔍 Show debug info"):
    assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
    st.write("Assistant:", assistant.name)
    st.write("Instructions:", assistant.instructions)
    st.write("Thread ID:", st.session_state.thread_id)
