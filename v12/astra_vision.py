import requests
import json
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from io import BytesIO
import os
from dotenv import load_dotenv

# ✅ Load API keys from .env file
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.getenv("GOOGLE_CX_ID")

print(f"🔹 Using Google CX ID: {GOOGLE_CX_ID}")  # Debugging

# ✅ Load CLIP model for image-to-text processing
print("✅ Loading CLIP model...")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("✅ CLIP model loaded successfully.")

def log(message):
    """Unified logging function for Astra's activities."""
    print(f"📜 DEBUG: {message}")

def fetch_google_image(query):
    """Fetch the first image result from Google Custom Search API."""
    log(f"🔎 Searching Google Images for: {query}")
    search_url = (
        f"https://www.googleapis.com/customsearch/v1?q={query}&cx={GOOGLE_CX_ID}"
        f"&key={GOOGLE_API_KEY}&searchType=image&num=1"
    )

    try:
        response = requests.get(search_url)
        data = response.json()

        if "items" in data and len(data["items"]) > 0:
            image_url = data["items"][0]["link"]
            log(f"🖼️ Found Image URL: {image_url}")
            return image_url
        else:
            log("⚠ No images found for query.")
            return None
    except Exception as e:
        log(f"❌ ERROR: Google Image Search Failed: {e}")
        return None

def analyze_image(image_url):
    """Fetch an image and generate a text description using CLIP."""
    if not image_url:
        return "No image available."

    log(f"🔍 Fetching image for analysis: {image_url}")
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content)).convert("RGB")

        # ✅ Provide possible text descriptions for comparison
        text_descriptions = [
            "a dog", "a cat", "a person", "a cityscape", 
            "a complex diagram", "a neural network illustration"
        ]

        # ✅ Properly tokenize text descriptions with padding & truncation
        text_inputs = clip_processor(text=text_descriptions, padding=True, truncation=True, return_tensors="pt")

        # ✅ Process the image correctly
        image_inputs = clip_processor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = clip_model(**{**text_inputs, **image_inputs})  # ✅ Merge image & text inputs

        # ✅ Get similarity scores
        similarity_scores = outputs.logits_per_image.softmax(dim=1).numpy()[0]
        best_match_index = similarity_scores.argmax()
        best_description = text_descriptions[best_match_index]

        log(f"📜 DEBUG: CLIP Image Analysis Output → {best_description}")
        return best_description
    except Exception as e:
        log(f"⚠ ERROR: Failed to analyze image → {e}")
        return None

