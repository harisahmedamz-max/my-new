import streamlit as st
from openai import OpenAI
import time

# Initialize client
client = OpenAI()

# Replace with your MacQuip Assistant ID from Playground
ASSISTANT_ID = "asst_PogREgRWsM0PHH6LqvV114YR"

# Create/persist thread in Streamlit session
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

st.title("Plaid-Libs™")

# Chat history UI
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if user_input := st.chat_input("Type your message..."):
    # Save and show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Send message to thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID,
    )

    # Poll until complete
    with st.chat_message("assistant"):
        placeholder = st.empty()
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled", "expired"]:
                placeholder.error("Run failed: " + run_status.status)
                st.stop()
            time.sleep(1)

        # Retrieve all messages from the thread
        messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)

        # Find the latest assistant reply
        for msg in messages.data:
            if msg.role == "assistant":
                reply = msg.content[0].text.value
                break

        # Display assistant reply
        placeholder.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})







