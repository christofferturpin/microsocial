import json
import boto3
import os
import time
from datetime import datetime
from botocore.exceptions import ClientError

print("Loading function...")
print("lambda with XSS filter, IP display, and CloudFront invalidation")

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

    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": cors_headers
        }

    try:
        claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
        user_id = claims.get("cognito:username") or claims.get("username")
        source_ip = event.get("requestContext", {}).get("http", {}).get("sourceIp", "Unknown")

        if not user_id:
            return {
                "statusCode": 403,
                "headers": cors_headers,
                "body": json.dumps({"error": "Unauthorized"})
            }

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

        # Basic XSS filter
        if any(tag in content.lower() for tag in ["<script", "<iframe", "<object", "<embed", "onerror"]):
            warning_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Nice Try</title>
  <style>
    body {{
      font-family: monospace;
      background-color: black;
      color: red;
      padding: 2rem;
    }}
    .container {{
      max-width: 600px;
      margin: auto;
      border: 2px solid red;
      padding: 1rem;
      background-color: #111;
    }}
    h1 {{
      color: yellow;
    }}
    .ip {{
      color: lightblue;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Nice Try :) </h1>
    <p>No XSS here. Your submission contained tags like &lt;script&gt;, &lt;iframe&gt;, or &lt;embed&gt;.</p>
    <p>I appericate the gumption, but go do hacktheboxes or something instead. You don't want the FBI breathing down your neck, trust me, it sucks.</p>
    <p class="ip">Your IP has been logged: <strong>{source_ip}</strong></p>
    <p>Try again without forbidden tags. Two more strikes and you're banned for 24 hours!</p>
    <p><em>– Chris.</em></p>
  </div>
</body>
</html>"""

            s3.put_object(
                Bucket="microsocial-site-051826702983",
                Key=f"u/{user_id}.html",
                Body=warning_html,
                ContentType="text/html"
            )

            cf.create_invalidation(
                DistributionId="E2IPL84OKE5F39",
                InvalidationBatch={
                    'Paths': {'Quantity': 1, 'Items': [f"/u/{user_id}.html"]},
                    'CallerReference': str(time.time())
                }
            )

            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"message": "Nice try, but no XSS!"})
            }

        # Save to DynamoDB
        table = dynamodb.Table(os.environ.get('PAGES_TABLE', 'Pages'))
        table.put_item(Item={
            "userId": user_id,
            "content": content,
            "webring": webring[:5],
            "lastUpdated": datetime.utcnow().isoformat()
        })

        # Build page HTML
        links_html = ""
        if webring:
            links_html += '<div class="webring"><h3>Web Ring</h3>'
            for link in webring[:5]:
                safe_link = link if link else "chris"
                links_html += f'<a href="https://microsocial.link/u/{safe_link}.html">{safe_link}</a><br>'
            links_html += '</div>'
        else:
            links_html = '<p><a href="https://microsocial.link/u/chris.html">Join the Webring</a></p>'

        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{user_id}'s Page</title>
  <style>
    body {{
      font-family: 'Courier New', monospace;
      background-color: #000033;
      color: #00FF99;
      padding: 2rem;
      background-image: url('https://www.transparenttextures.com/patterns/stardust.png');
      background-repeat: repeat;
    }}
    h1 {{
      color: #FFD700;
      text-shadow: 1px 1px 0 #FF00FF;
    }}
    pre {{
      white-space: pre-wrap;
      background-color: #111;
      border: 2px dashed #00FFFF;
      padding: 1rem;
      box-shadow: 0 0 10px #00FFFF;
    }}
    a {{
      color: #00FFFF;
      font-weight: bold;
      text-decoration: underline;
    }}
    .webring {{
      margin-top: 2rem;
      padding: 1rem;
      border: 2px dashed #FF00FF;
      background-color: #111111cc;
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }}
    .webring h3 {{
      flex-basis: 100%;
      color: #FFD700;
      margin-bottom: 0.5rem;
    }}
    .webring a {{
      display: inline-block;
      padding: 0.4rem 0.7rem;
      border: 1px dashed #FFD700;
      background-color: #222;
      color: #00FFFF;
      text-decoration: none;
    }}
    .webring a:hover {{
      background-color: #FF00FF;
      color: #000;
    }}
  </style>
</head>
<body>
  <h1>{user_id}'s Page</h1>
  <pre>{content}</pre>
  {links_html}
  <p><a href="https://microsocial.link">Back to MicroSocial</a></p>
</body>
</html>"""

        s3.put_object(
            Bucket="microsocial-site-051826702983",
            Key=f"u/{user_id}.html",
            Body=html,
            ContentType="text/html"
        )

        cf.create_invalidation(
            DistributionId="E2IPL84OKE5F39",
            InvalidationBatch={
                'Paths': {'Quantity': 1, 'Items': [f"/u/{user_id}.html"]},
                'CallerReference': str(time.time())
            }
        )

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"message": "Page saved and published!"})
        }

    except ClientError as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": "AWS service error."})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": "Unexpected server error."})
        }
