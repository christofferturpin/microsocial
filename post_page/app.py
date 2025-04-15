import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

print("Loading function...")
print("most recent version of lambda")

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def build_cors_headers(origin):
    allowed_origins = ["https://microsocial.link", "https://www.microsocial.link"]
    return {
        "Access-Control-Allow-Origin": origin if origin in allowed_origins else "https://microsocial.link",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }

def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    origin = event.get("headers", {}).get("origin", "")
    cors_headers = build_cors_headers(origin)

    print("HTTP Method:", method)
    print("Received event:", json.dumps(event))

    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": cors_headers
        }

    try:
        claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
        user_id = claims.get("cognito:username") or claims.get("username")
        if not user_id:
            return {
                "statusCode": 403,
                "headers": cors_headers,
                "body": json.dumps({"error": "Unauthorized"})
            }

        print(f"Using Cognito username: {user_id}")

        # Parse body
        raw_body = event.get("body", "{}")
        body = json.loads(raw_body) if isinstance(raw_body, str) else (raw_body or {})
        content = body.get("content", "").strip()

        if not content:
            return {
                "statusCode": 400,
                "headers": cors_headers,
                "body": json.dumps({"error": "Missing or empty 'content'"})
            }

        # Save to DynamoDB
        table_name = os.environ.get('PAGES_TABLE', 'Pages')
        table = dynamodb.Table(table_name)
        table.put_item(Item={
            "userId": user_id,
            "content": content,
            "lastUpdated": datetime.utcnow().isoformat()
        })

        # Generate HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{user_id}'s Page</title>
            <style>
                body {{ font-family: sans-serif; background: #111; color: #eee; padding: 2rem; }}
            </style>
        </head>
        <body>
            <h1>{user_id}'s Page</h1>
            <pre>{content}</pre>
        </body>
        </html>
        """.strip()

        # Upload HTML to S3
        s3.put_object(
            Bucket="microsocial-site-051826702983",
            Key=f"u/{user_id}.html",
            Body=html,
            ContentType="text/html",
        )

        print(f"Uploaded static page for {user_id} to S3.")

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"message": "Page saved and published!"})
        }

    except ClientError as e:
        print("AWS error:", e)
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": "AWS service error."})
        }
    except Exception as e:
        print("Unexpected error:", e)
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": "Unexpected server error."})
        }
