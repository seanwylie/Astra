import requests
import json

def summarize_remote_mind_file(url, sample_size=2):
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    print(f"\n🔍 Summary of {url}\n{'='*40}")
    for key, value in data.items():
        print(f"\n🧠 Key: {key}")

        if isinstance(value, list):
            print(f"  📦 Type: List ({len(value)} entries)")
            print("  📑 Sample entries:")
            for i, item in enumerate(value[:sample_size]):
                short = json.dumps(item, indent=2)[:500]
                print(f"    {i+1}. {short}...\n")

        elif isinstance(value, dict):
            print(f"  📦 Type: Dict ({len(value)} keys)")
            sample_keys = list(value.keys())[:sample_size]
            print("  🧪 Sample keys/values:")
            for k in sample_keys:
                short = json.dumps(value[k], indent=2)[:300]
                print(f"    - {k}: {short}...\n")

        else:
            print(f"  📦 Value: {value} ({type(value).__name__})")

# Run it like this:
summarize_remote_mind_file("https://swylie-astra.s3.us-east-1.amazonaws.com/mind_file.json")

