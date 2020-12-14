import json
from base64 import b64encode
from uuid import uuid4

from decouple import config

from core.clients import sns_client


def delete_image(image_id, image_folder):
    sns_client.publish(
        TopicArn=config('IMAGE_TOPIC_ARN'),
        Message=json.dumps({'action': 'delete', 'image_id': image_id, 'image_folder': image_folder}),
    )


def upload_image(validated_data, image_folder):
    image = validated_data.pop(f'{image_folder}_image')
    image.name = str(uuid4())
    validated_data[f'{image_folder}_image_uuid'] = image.name

    image_bytes = image.read()
    image_base64 = b64encode(image_bytes)

    sns_client.publish(
        TopicArn=config('IMAGE_TOPIC_ARN'),
        Message=json.dumps(
            {'action': 'upload', 'image_base64': image_base64.decode('utf-8'), 'image_id': image.name,
             'image_folder': image_folder}),
    )

    return validated_data
