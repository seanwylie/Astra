from bs4 import BeautifulSoup
import requests

def test_google_images(query):
    """Fetch the first Google Image result for a given query."""
    search_url = f"https://www.google.com/search?tbm=isch&q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # 🔍 Find ALL image elements
        image_elements = soup.find_all("img")

        # 🔍 Print out all image URLs to debug
        print("\n🔎 **ALL SCRAPED IMAGE URLS:**")
        for img in image_elements:
            print("👉", img.get("src", ""))

    except Exception as e:
        print(f"❌ ERROR: Google Image Search Failed: {e}")

# ✅ Run the test
test_google_images("artificial intelligence")

