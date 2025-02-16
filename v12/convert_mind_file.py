import pandas as pd
import json

# Define file paths
xlsx_file = "/home/ubuntu/astra_reflections/mind_file_9.5_backup.xlsx"
json_file_path = "/home/ubuntu/astra_reflections/mind_file.json"

try:
    # Load the Excel file
    df = pd.read_excel(xlsx_file, engine="openpyxl")

    # Check if the file has data
    if df.empty:
        print("Error: The Excel file is empty.")
    else:
        # Convert to JSON format
        mind_file_json = df.to_dict(orient="records")

        # Save as JSON
        with open(json_file_path, "w") as json_file:
            json.dump({"past_reflections": mind_file_json}, json_file, indent=4)

        print(f"Conversion complete. JSON saved at: {json_file_path}")

except Exception as e:
    print(f"Error converting file: {e}")
