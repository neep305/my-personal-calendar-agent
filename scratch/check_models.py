import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_SESSION_TOKEN

session_kwargs = {
    "aws_access_key_id": AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
    "region_name": AWS_REGION
}
if AWS_SESSION_TOKEN:
    session_kwargs["aws_session_token"] = AWS_SESSION_TOKEN

client = boto3.client("bedrock", **session_kwargs)

try:
    print("=== Inference Profiles ===")
    profiles = client.list_inference_profiles()
    for p in profiles.get("inferenceProfileSummaries", []):
        if "claude" in p["inferenceProfileId"].lower():
            print(f"- {p['inferenceProfileId']} ({p['inferenceProfileName']})")
except Exception as e:
    print("Inference profiles error:", e)

try:
    print("\n=== Foundation Models ===")
    models = client.list_foundation_models(byProvider="Anthropic")
    for m in models.get("modelSummaries", []):
        print(f"- {m['modelId']} ({m['modelName']})")
except Exception as e:
    print("Foundation models error:", e)
