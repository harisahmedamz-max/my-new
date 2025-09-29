from openai import OpenAI

client = OpenAI()

assistant = client.beta.assistants.retrieve("asst_PogREgRWsM0PHH6LqvV114YR")

thread = client.beta.threads.create()

client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Hello, can you help me track my order?"
)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id
)

messages = client.beta.threads.messages.list(thread_id=thread.id)
for m in messages.data:
    print(m.role, ":", m.content[0].text.value)
