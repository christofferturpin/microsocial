import boto3
import os
import random
import json

s3 = boto3.client('s3')
BUCKET_NAME = os.environ['SITE_BUCKET']

def lambda_handler(event, context):
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="u/")
        all_keys = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.html')]

        random_keys = random.sample(all_keys, min(5, len(all_keys)))
        user_links = [f"https://microsocial.link/{key}" for key in random_keys]

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps(user_links)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
