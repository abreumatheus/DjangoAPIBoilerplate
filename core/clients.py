import boto3
from decouple import config

sns_client_options = {
    'region_name': config('AWS_DEFAULT_REGION'),
    'aws_access_key_id': config('AWS_ACCESS_KEY_ID'),
    'aws_secret_access_key': config('AWS_SECRET_ACCESS_KEY'),
    'endpoint_url': config('AWS_ENDPOINT_URL'),
}

sns_client = boto3.client('sns', **sns_client_options)
