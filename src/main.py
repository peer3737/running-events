import requests
import os
import json
import boto3
import logging
from supporting import aws


formatter = logging.Formatter('[%(levelname)s] %(message)s')
log = logging.getLogger()
log.setLevel("INFO")
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
for handler in log.handlers:
    log.removeHandler(handler)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)


def lambda_handler(event, context):
    lambda_client = boto3.client('lambda')
    events = aws.dynamodb_query('events')
    for event in events:
        event_id = event['id']
        event_name = event['name']
        log.info(event_name)
        response = requests.get(event['url'])
        if event['open_text'] in response.text:
            log.info(f"Inschrijving {event_name} is geopend")
            payload = {
                "to": os.environ['MAIL_CONTACT'],
                "from": os.environ['MAIL_SENDER'],
                "subject": f"Inschrijving voor {event_name} is geopend",
                "content": f"Inschrijving voor {event_name} is geopend. Ga naar {event['url']}"
            }

            lambda_client.invoke(
                FunctionName='sendMail',  # Replace with the name of your sendMail function
                InvocationType='Event',  # Use 'RequestResponse' for synchronous invocation
                Payload=json.dumps(payload)
            )
            aws.dynamo_db_update('events', item_id=event_id, attribute='check', value=False)
    return None


