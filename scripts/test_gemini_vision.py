import os
import google.generativeai as genai
import PIL.Image

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

img = PIL.Image.open("screenshot.png")
response = model.generate_content(
    ["Read all the text visible in this screenshot.", img]
)

print(response.text)
