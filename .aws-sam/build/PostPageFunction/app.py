import json
import boto3
import os
import time
from datetime import datetime
from botocore.exceptions import ClientError

print("Loading function...")
print("most recent version of lambda with webring")

s3 = boto3.client('s3')
cf = boto3.client('cloudfront')
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
        webring = body.get("links", [])

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
            "webring": webring[:5],
            "lastUpdated": datetime.utcnow().isoformat()
        })

        # Build HTML for static page
        links_html = ""
        if webring:
            links_html += "<h2>Webring</h2><ul>"
            for link in webring[:5]:
                safe_link = link if link else "chris"
                links_html += f'<li><a href="https://microsocial.link/u/{safe_link}.html">{safe_link}</a></li>'
            links_html += "</ul>"
        else:
            links_html = '<p><a href="https://microsocial.link/u/chris.html">Join the Webring</a></p>'

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{user_id}'s Page</title>
            <style>
                body {{ font-family: sans-serif; background: #111; color: #eee; padding: 2rem; }}
                a {{ color: #00f }}
            </style>
        </head>
        <body>
            <h1>{user_id}'s Page</h1>
            <pre>{content}</pre>
            {links_html}
        </body>
        </html>
        """.strip()

        # Upload HTML to S3
        s3.put_object(
            Bucket="microsocial-site-051826702983",
            Key=f"u/{user_id}.html",
            Body=html,
            ContentType="text/html"
        )

        print(f"Uploaded static page for {user_id} to S3.")

        # Invalidate CloudFront cache
        cf.create_invalidation(
            DistributionId="E2IPL84OKE5F39",
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': [f"/u/{user_id}.html"]
                },
                'CallerReference': str(time.time())
            }
        )

        print(f"Invalidated CloudFront path: /u/{user_id}.html")

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
