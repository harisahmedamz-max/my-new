import streamlit as st
from openai import OpenAI

client = OpenAI()

# 👉 Replace with your Playground Assistant ID
ASSISTANT_ID = "asst_PogREgRWsM0PHH6LqvV114YR"

st.title("🔍 Assistant Debugger")

# Step 1. Retrieve assistant details
assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
st.write("✅ Assistant Loaded:", assistant.name)
st.write("📝 Instructions:", assistant.instructions)

# Step 2. Create a fresh thread each run
thread = client.beta.threads.create()
st.write("🧵 Thread ID:", thread.id)

# Step 3. Input box
user_input = st.text_input("Type a test message:")

if user_input:
    # Add user message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input,
    )

    # Run the assistant
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
    )

    # Get all messages (raw)
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    st.subheader("📥 Raw API Messages")
    st.json(messages.dict())

    # Extract last assistant reply
    reply = None
    for m in reversed(messages.data):
        if m.role == "assistant":
            reply = m.content[0].text.value
            break

    if reply:
        st.subheader("🤖 Assistant Reply")
        st.write(reply)




