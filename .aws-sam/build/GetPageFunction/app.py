import json
import boto3
import os
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PAGES_TABLE'])

def lambda_handler(event, context):
    try:
        username = event['pathParameters'].get('username')

        if not username:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing username in path"})
            }

        # Look up by userId (we're treating username = userId for now)
        response = table.get_item(Key={'userId': username})

        if 'Item' not in response:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "User page not found"})
            }

        return {
            "statusCode": 200,
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
            "body": json.dumps({"error": "Server error retrieving page."})
        }
    except Exception as e:
        print("Unexpected error:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Unexpected server error."})
        }
