from groq import Groq

client = Groq(api_key="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")
r = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "hi"}]
)
print("Works:", r.choices[0].message.content)