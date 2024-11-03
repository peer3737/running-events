import requests
import os
import json
import boto3


events = {
    "CPC": {
        "check": True,
        "url": "https://nncpcloopdenhaag.nl/inschrijven/",
        "open_text": "https://in.njuko.com"
    },
    "Utrecht marathon": {
        "check": False,
        "url": "https://utrechtmarathon.com/inschrijven/",
        "open_text": "https://in.njuko.com"
    }
}



def lambda_handler(event, context):
    lambda_client = boto3.client('lambda')

    for event in events:
        if events[event]['check']:
            response = requests.get(events[event]['url'])
            if events[event]['open_text'] in response.text:
                payload = {
                    "to": os.environ['MAIL_CONTACT'],
                    "subject": "JSON files not created and uploaded to S3",
                    "content": f"Inschrijving voor {event} is geopend"
                }

                lambda_client.invoke(
                    FunctionName='sendMail',  # Replace with the name of your sendMail function
                    InvocationType='Event',  # Use 'RequestResponse' for synchronous invocation
                    Payload=json.dumps(payload)
                )
    return None


