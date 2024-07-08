from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv()
acct_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

def send_whatsapp(phone_number, message):
    ## If workout plan is created, send Whatsapp message informing the user
    client = Client(acct_sid, auth_token)
    message = client.messages.create(
        from_='whatsapp:+14155238886',
        body=message,
        to='whatsapp:'+phone_number,)
def main():
    send_whatsapp("+917676912381", "Hello world")

if __name__ == "__main__":
    main()
