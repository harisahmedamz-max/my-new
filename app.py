import streamlit as st
from openai import OpenAI

# Initialize client
client = OpenAI()

# Your assistant ID from Playground
ASSISTANT_ID = "asst_PogREgRWsM0PH6LqvV114YR"

# Initialize session state
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []  # store conversation history

st.title("💬 My Custom Assistant")

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Save user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Send user message to assistant
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input,
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    # Get latest messages
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)

    # Add assistant reply to session
    for m in reversed(messages.data):
        if m.role == "assistant":
            reply = m.content[0].text.value
            st.session_state.messages.append({"role": "assistant", "content": reply})
            break

# Display conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
