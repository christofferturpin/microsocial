import json

def lambda_handler(event, context):
    body = json.loads(event["body"])
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Hello {body.get('content')}, this would be saved!"
        })
    }
