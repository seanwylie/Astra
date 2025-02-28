import boto3
import json

# S3 Configuration
bucket_name = "swylie-astra"
file_key = "mind_file.json"

# Initialize S3 client
s3 = boto3.client("s3")

# Download and load mind_file.json
print("🔍 Fetching mind file from S3...")
response = s3.get_object(Bucket=bucket_name, Key=file_key)
mind_data = json.loads(response["Body"].read().decode())

# 🛠 Cleanup Steps:
print("🧹 Cleaning up mind file...")

# ✅ Reset corrupted/questionable sections
mind_data["self_questions"] = []
mind_data["unresolved_questions"] = []

# ✅ Deduplicate reflections & knowledge
mind_data["self_reflections"] = list(set(mind_data.get("self_reflections", [])))
mind_data["stored_knowledge"] = list(set(mind_data.get("stored_knowledge", [])))

# ✅ Save cleaned file back to S3
s3.put_object(Bucket=bucket_name, Key=file_key, Body=json.dumps(mind_data, indent=4))
print("✅ Mind file cleaned and updated in S3!")
