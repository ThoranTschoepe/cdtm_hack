from google import genai
from google.genai import types
import base64

def get_image_locally(image_path: str):
  # Read the image file and encode it as base64
  with open(image_path, "rb") as image_file:
      image_bytes = image_file.read()
      base64_encoded = base64.b64encode(image_bytes).decode('utf-8')

  # Create the message part from the image
  msg1_image1 = types.Part.from_bytes(
      data=base64.b64decode(base64_encoded),
      mime_type="image/jpeg",
  )

  return msg1_image1


def categorize_picture():
  client = genai.Client(
      vertexai=True,
      project="avi-cdtm-hack-team-9800",
      location="us-central1",
  )

  msg1_image1 = get_image_locally("data/IMG_0417.jpg")

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

def parse_lab_report():
  client = genai.Client(
      vertexai=True,
      project="avi-cdtm-hack-team-9800",
      location="us-central1",
  )

  msg1_image1 = get_image_locally("data/IMG_2221.jpg")

  model = "gemini-2.0-flash-001"
  contents = [
    types.Content(
      role="user",
      parts=[
        msg1_image1,
        types.Part.from_text(text="""extract data as the json schema""")
      ]
    ),
  ]
  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 0.95,
    max_output_tokens = 8192,
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
    response_schema = {"type":"OBJECT","properties":{"report_metadata":{"type":"OBJECT","properties":{"lab_name":{"type":"STRING"},"report_date":{"type":"STRING"},"report_id":{"type":"STRING"}}},"patient_information":{"type":"OBJECT","properties":{"name":{"type":"STRING"},"id":{"type":"STRING"},"date_of_birth":{"type":"STRING"},"gender":{"type":"STRING"}},"required":["name","id"]},"test_results":{"type":"ARRAY","items":{"type":"OBJECT","properties":{"test_name":{"type":"STRING"},"test_category":{"type":"STRING"},"test_code":{"type":"STRING","nullable":True},"value":{"type":"STRING"},"unit":{"type":"STRING"},"reference_range":{"type":"OBJECT","properties":{"lower_limit":{"type":"STRING","nullable":True},"upper_limit":{"type":"STRING","nullable":True},"text_range":{"type":"STRING","nullable":True}}},"flag":{"type":"STRING","enum":["normal","low","high","critical_low","critical_high","abnormal","not_applicable"],"nullable":True},"comments":{"type":"STRING","nullable":True}},"required":["test_name","value"]}},"interpretation":{"type":"STRING","nullable":True}},"required":["patient_information","test_results"]},
  )

  for chunk in client.models.generate_content_stream(
    model = model,
    contents = contents,
    config = generate_content_config,
    ):
    print(chunk.text, end="")

#categorize_picture()
parse_lab_report()