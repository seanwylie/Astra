from astra_vision import fetch_google_image, analyze_image

test_query = "Dog"

print(f"🔍 Testing Google Image Search for: {test_query}")
image_url = fetch_google_image(test_query)
print(f"🖼️ Image URL: {image_url}")

if image_url:
    print("🔎 Testing CLIP Image Analysis...")
    description = analyze_image(image_url)
    print(f"📜 Image Description: {description}")
