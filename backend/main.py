from google import genai
from google.genai import types
import base64

def generate():
  client = genai.Client(
      vertexai=True,
      project="avi-cdtm-hack-team-9800",
      location="us-central1",
  )

  # Path to your image
  image_path = "data/IMG_0417.jpg"

  # Read the image file and encode it as base64
  with open(image_path, "rb") as image_file:
      image_bytes = image_file.read()
      base64_encoded = base64.b64encode(image_bytes).decode('utf-8')

  # Create the message part from the image
  msg1_image1 = types.Part.from_bytes(
      data=base64.b64decode(base64_encoded),
      mime_type="image/jpeg",
  )

  model = "gemini-2.5-pro-preview-05-06"
  contents = [
    types.Content(
      role="user",
      parts=[
        msg1_image1,
        types.Part.from_text(text="""categorize this as either \"medications\", \"allergies\", \"diagnoses\", \"lab_results\"""")
      ]
    ),
  ]
  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 1,
    seed = 0,
    max_output_tokens = 65535,
    response_modalities = ["TEXT"],
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )],
    response_mime_type = "application/json",
    response_schema = {"type":"OBJECT","properties":{"object":{"type":"STRING"}}},
  )

  for chunk in client.models.generate_content_stream(
    model = model,
    contents = contents,
    config = generate_content_config,
    ):
    print(chunk.text, end="")

generate()