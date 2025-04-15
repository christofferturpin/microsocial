import json
import boto3
import os
from botocore.exceptions import ClientError

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",  # Replace with your domain in prod
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
}

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PAGES_TABLE'])

def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")

    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": CORS_HEADERS
        }

    try:
        claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
        print("JWT Claims:", json.dumps(claims))

        user_id = claims.get("username")


        if not user_id:
            return {
                "statusCode": 403,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Unauthorized"})
            }

        response = table.get_item(Key={'userId': user_id})

        if 'Item' not in response:
            return {
                "statusCode": 404,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Your page was not found."})
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "userId": response['Item']['userId'],
                "content": response['Item']['content'],
                "lastUpdated": response['Item']['lastUpdated']
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Server error retrieving your page."})
        }
    except Exception as e:
        print("Unexpected error:", e)
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Unexpected server error."})
        }
