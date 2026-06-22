import asyncio
import base64
import os
from google import genai
from google.genai import types

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
CLAUDE_KEY = os.environ["ANTHROPIC_API_KEY"]

PROMPT = """아래 JSON만 반환하라.

{
  "is_ai_generated": true,
  "score": 0.5,
  "confidence": "low",
  "evidence": [],
  "limitations": []
}"""

png_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
)

async def test_gemini():
    client = genai.Client(api_key=GEMINI_KEY)
    image_part = types.Part.from_bytes(data=png_1x1, mime_type="image/png")
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[PROMPT, image_part],
    )
    print("=== GEMINI RAW ===")
    print(repr(response.text[:500]))

async def test_claude():
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=CLAUDE_KEY)
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.b64encode(png_1x1).decode()}},
                {"type": "text", "text": PROMPT},
            ]
        }]
    )
    print("=== CLAUDE RAW ===")
    print(repr(response.content[0].text[:500]))

async def main():
    await test_gemini()
    await test_claude()

asyncio.run(main())
