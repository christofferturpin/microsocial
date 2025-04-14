import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

print("Loading function...")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
}

def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    print("HTTP Method:", method)
    print("Received event:", json.dumps(event))

    # Handle preflight CORS check
    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": CORS_HEADERS
        }

    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('PAGES_TABLE', 'Pages')
        table = dynamodb.Table(table_name)
        print(f"Using DynamoDB table: {table_name}")

        raw_body = event.get("body", "{}")
        body = json.loads(raw_body) if isinstance(raw_body, str) else (raw_body or {})

        content = body.get("content", "").strip()
        if not content:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Missing or empty 'content'"})
            }

        user_id = "user-123"  # Replace with real user ID from Cognito later

        table.put_item(Item={
            "userId": user_id,
            "content": content,
            "lastUpdated": datetime.utcnow().isoformat()
        })

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "Page saved successfully."})
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Server error when saving page."})
        }
    except Exception as e:
        print("Unexpected error:", e)
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Unexpected server error."})
        }
