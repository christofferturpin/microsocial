import boto3
import json
import sys

distribution_id = "E2IPL84OKE5F39"
origin_id = "SiteBucketOrigin"
path_pattern = "/u/*"
response_headers_policy_name = "MicroSocialSecurityHeaders"

cf = boto3.client('cloudfront')

# Step 1: Create or get ResponseHeadersPolicy
print("Checking for existing ResponseHeadersPolicy...")
existing = cf.list_response_headers_policies(Type='custom')
policy_id = None

for item in existing['ResponseHeadersPolicyList']['Items']:
    if item['ResponseHeadersPolicy']['ResponseHeadersPolicyConfig']['Name'] == response_headers_policy_name:
        policy_id = item['ResponseHeadersPolicy']['Id']
        break

if not policy_id:
    print("Creating new ResponseHeadersPolicy...")
    result = cf.create_response_headers_policy(
        ResponseHeadersPolicyConfig={
            "Name": response_headers_policy_name,
            "Comment": "Security headers for /u/* behavior",
            "SecurityHeadersConfig": {
                "ContentSecurityPolicy": {
                    "ContentSecurityPolicy": "default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; frame-src https://www.youtube.com https://www.youtube-nocookie.com; media-src https:; object-src 'none'; base-uri 'none';",
                    "Override": True
                },
                "ReferrerPolicy": {
                    "ReferrerPolicy": "strict-origin-when-cross-origin",
                    "Override": True
                },
                "CustomHeadersConfig": {
                    "Items": [
                        {
                            "Header": "X-Frame-Options",
                            "Value": "DENY",
                            "Override": True
                        },
                        {
                            "Header": "X-Content-Type-Options",
                            "Value": "nosniff",
                            "Override": True
                        }
                    ]
                }
            }
        }
    )
    policy_id = result['ResponseHeadersPolicy']['Id']
    print("Created policy ID:", policy_id)
else:
    print("Found existing policy ID:", policy_id)

# Step 2: Get distribution config
print("Fetching CloudFront config...")
resp = cf.get_distribution_config(Id=distribution_id)
config = resp['DistributionConfig']
etag = resp['ETag']

# Step 3: Patch cache behavior
print(f"Updating cache behavior for path: {path_pattern}")
behaviors = config.get("CacheBehaviors", {"Quantity": 0, "Items": []})

# Remove any existing /u/* behavior
behaviors["Items"] = [
    b for b in behaviors.get("Items", []) if b.get("PathPattern") != path_pattern
]

behaviors["Items"].append({
    "PathPattern": path_pattern,
    "TargetOriginId": origin_id,
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": ["GET", "HEAD"],
    "CachedMethods": ["GET", "HEAD"],
    "Compress": True,
    "CachePolicyId": "413fdccd-01c1-4af6-bb5b-dacbc1f82c6d",
    "ResponseHeadersPolicyId": policy_id
})

behaviors["Quantity"] = len(behaviors["Items"])
config["CacheBehaviors"] = behaviors

# Step 4: Push the update
print("Pushing updated config to CloudFront...")
cf.update_distribution(
    Id=distribution_id,
    DistributionConfig=config,
    IfMatch=etag
)

print(" Update complete!")
