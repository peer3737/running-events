import requests
import os
import json
import boto3
import logging
from supporting import aws

# Logging setup
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

# SES client
ses = boto3.client('ses', region_name='eu-central-1')  # pas regio aan indien nodig

def send_mail(to_address, subject, body_text, body_html):
    """Verstuur een e-mail via Amazon SES, met tekst en HTML versie"""
    try:
        response = ses.send_email(
            Source=os.environ['MAIL_SENDER'],  # geverifieerd e-mail adres of domein in SES
            Destination={'ToAddresses': [to_address]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text},
                    'Html': {'Data': body_html}
                }
            }
        )
        log.info(f"E-mail verzonden naar {to_address}")
        return response
    except Exception as e:
        log.error(f"Fout bij verzenden naar {to_address}: {e}")
        return None

def lambda_handler(event, context):
    # Ophalen van events uit DynamoDB
    events = aws.dynamodb_query('events')

    for event_item in events:
        check = event_item.get('check', False)
        if check:
            event_id = event_item['id']
            event_name = event_item['name']
            subs = event_item['subs']
            log.info(f"Controle voor event: {event_name}")

            # Check of inschrijving open is
            try:
                response = requests.get(event_item['url'], timeout=10)
                if event_item['open_text'].lower() in response.text.lower():
                    log.info(f"Inschrijving {event_name} is MOGELIJK geopend")
                    for sub in subs:
                        subject = f"Inschrijving voor {event_name} is MOGELIJK geopend"
                        body_text = f"Inschrijving voor {event_name} is geopend. De inschrijfpagina is relevant gewijzigd. Ga naar {event_item['url']}"
                        body_html = f"""
                        <html>
                        <body>
                            <p>Inschrijving voor <b>{event_name}</b> is MOGELIJK geopend!</p>
                            <p>De inschrijfpagina is relevant gewijzigd</p>
                            <p>Ga naar <a href="{event_item['url']}">{event_item['url']}</a> om je in te schrijven.</p>
                        </body>
                        </html>
                        """
                        send_mail(sub, subject, body_text, body_html)

                    # Update DynamoDB om check uit te zetten
                    aws.dynamo_db_update('events', item_id=event_id, attribute='check', value=False)
            except requests.RequestException as e:
                log.error(f"Fout bij ophalen URL {event_item['url']}: {e}")

    return {"status": "completed"}
