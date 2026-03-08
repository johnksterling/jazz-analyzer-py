import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class ChordExtraction(BaseModel):
    chord_symbol: str = Field(description="The jazz chord symbol, e.g. Eb7#9, Abm11")
    horizontal_percentage: float = Field(description="Estimated horizontal position from left to right (0.0 to 1.0)")

class ChordList(BaseModel):
    chords: list[ChordExtraction]

def extract_chords_with_ai(image_path):
    """
    Uses Gemini Vision to extract jazz chord symbols and their relative positions
     from a staff system image snippet.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment. AI extraction skipped.")
        return []

    client = genai.Client(api_key=api_key)
    
    # Upload the slice
    uploaded_file = client.files.upload(file=image_path)

    prompt = (
        "You are an expert jazz musician. Look at this snippet of a lead sheet staff. "
        "Extract the chord symbols written above the staff from left to right. "
        "Ignore the melody notes and staff lines. "
        "Return them as a JSON list along with their approximate horizontal position "
        "from 0.0 (far left) to 1.0 (far right)."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ChordList,
                temperature=0.0,
            ),
        )
        
        # Parse the JSON response
        data = ChordList.model_validate_json(response.text)
        return data.chords
    except Exception as e:
        print(f"AI Extraction failed for {image_path}: {e}")
        return []
    finally:
        # Cleanup file from Google Cloud
        try:
            client.files.delete(name=uploaded_file.name)
        except:
            pass
