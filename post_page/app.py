import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

print("Loading function...")

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))  # 🔍 Log full event
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('PAGES_TABLE', 'Pages')
        print("Using table:", table_name)
        table = dynamodb.Table(table_name)

        body = json.loads(event.get("body", "{}"))
        content = body.get("content", "").strip()

        if not content:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing or empty 'content'"})
            }

        user_id = "user-123"

        item = {
            "userId": user_id,
            "content": content,
            "lastUpdated": datetime.utcnow().isoformat()
        }

        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Page saved successfully."})
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Server error when saving page."})
        }
    except Exception as e:
        print("Unexpected error:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Unexpected server error."})
        }
