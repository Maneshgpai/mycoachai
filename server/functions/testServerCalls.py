from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
ist = timezone(timedelta(hours=5, minutes=30))

load_dotenv()
acct_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

def send_whatsapp_msging_srvc(phone_number, message):
    ## If workout plan is created, send Whatsapp message informing the user
    client = Client(acct_sid, auth_token)
    message = client.messages.create(
        messaging_service_sid="MG5700d70eef672a1bbbfd5091fef1d963",
        body=message,
        to='whatsapp:'+phone_number,)

def send_whatsapp_sandbox(phone_number, message):
    ## If workout plan is created, send Whatsapp message informing the user
    client = Client(acct_sid, auth_token)
    message = client.messages.create(
        from_="whatsapp:+14155238886",
        to='whatsapp:'+phone_number,
        body=message,)

def send_whatsapp_sender(phone_number, message):
    ## If workout plan is created, send Whatsapp message informing the user
    client = Client(acct_sid, auth_token)
    message = client.messages.create(
        from_="whatsapp:+917676912381",
        to='whatsapp:'+phone_number,
        body=message,)
    
def main():
    send_whatsapp_msging_srvc("+919633528888", f"The time is {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"The time is {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}")
if __name__ == "__main__":
    main()
