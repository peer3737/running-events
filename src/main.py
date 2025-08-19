import requests
import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supporting import aws

# Logging setup
formatter = logging.Formatter('[%(levelname)s] %(message)s')
log = logging.getLogger()
log.setLevel("INFO")
for handler in log.handlers:
    log.removeHandler(handler)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)

def send_gmail(to_address, subject, body_text, body_html):
    """Verstuur e-mail via Gmail SMTP (App Password)"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = os.environ['MAIL_SENDER']
        msg['To'] = to_address

        # Voeg text en HTML toe
        part1 = MIMEText(body_text, 'plain')
        part2 = MIMEText(body_html, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Verstuur via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(os.environ['MAIL_SENDER'], "lede yepw pgeb gmha")
            server.sendmail(os.environ['MAIL_SENDER'], to_address, msg.as_string())
        log.info(f"E-mail verzonden naar {to_address}")
    except Exception as e:
        log.error(f"Fout bij verzenden naar {to_address}: {e}")

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

            # Check of inschrijving open is (case-insensitive)
            try:
                response = requests.get(event_item['url'], timeout=10)
                if event_item['open_text'].lower() in response.text.lower():
                    log.info(f"Inschrijving {event_name} is MOGELIJK geopend")
                    for sub in subs:
                        subject = f"Inschrijving voor {event_name} is MOGELIJK geopend"
                        body_text = f"Inschrijving voor {event_name} is MOGELIJK geopend. Er is iets relevants gewijzigd aan de inschrijfpagina. Ga naar {event_item['url']}"
                        body_html = f"""
                        <html>
                        <body>
                            <p>Inschrijving voor <b>{event_name}</b> is MOGELIJK geopend!</p>
                            <p>Er is iets relevants gewijzigd aan de inschrijfpagina</p>
                            <p>Ga naar <a href="{event_item['url']}">{event_item['url']}</a> om je in te schrijven.</p>
                        </body>
                        </html>
                        """
                        send_gmail(sub, subject, body_text, body_html)

                    # Update DynamoDB om check uit te zetten
                    aws.dynamo_db_update('events', item_id=event_id, attribute='check', value=False)
            except requests.RequestException as e:
                log.error(f"Fout bij ophalen URL {event_item['url']}: {e}")

    return {"status": "completed"}
