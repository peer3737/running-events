import requests
import os
import json
import boto3
import logging


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
    events = {
        "CPC": {
            "check": True,
            "url": "https://nncpcloopdenhaag.nl/inschrijven/",
            "open_text": "https://in.njuko.com"
        },
        "Utrecht marathon": {
            "check": True,
            "url": "https://utrechtmarathon.com/inschrijven/",
            "open_text": "https://in.njuko.com"
        }
    }
    for event in events:
        if events[event]['check']:
            log.info(event)
            response = requests.get(events[event]['url'])
            if events[event]['open_text'] in response.text:
                payload = {
                    "to": os.environ['MAIL_CONTACT'],
                    "from": os.environ['MAIL_SENDER'],
                    "subject": f"Inschrijving voor {event} is geopend",
                    "content": f"Inschrijving voor {event} is geopend. Ga naar {events[event]['url']}"
                }

                lambda_client.invoke(
                    FunctionName='sendMail',  # Replace with the name of your sendMail function
                    InvocationType='Event',  # Use 'RequestResponse' for synchronous invocation
                    Payload=json.dumps(payload)
                )
    return None


