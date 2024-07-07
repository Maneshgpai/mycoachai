from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv()


def json_to_human_readable(data, prefix=""):
    result = []
    if isinstance(data, dict):
        for key, value in data.items():
            if "language" in key.lower():
                vLanguage = value
            if "pii" not in key.lower() and "language" not in key.lower():
                if isinstance(value, (dict, list)):
                    result.append(f"{key.capitalize()}=")
                    result.append(json_to_human_readable(value, prefix + key + "_"))
                else:
                    result.append(f"{key.capitalize()}= {value}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            result.append(f"Item {i + 1}=")
            result.append(json_to_human_readable(item, prefix + "item" + str(i + 1) + "_"))
    else:
        result.append(f"{data}")
    return ";".join(result)

def get_user_health_profile(data, prefix=""):
    result = []
    if isinstance(data, dict):
        for key, value in data.items():
            if "pii" not in key.lower() and "language" not in key.lower():
                if isinstance(value, (dict, list)):
                    result.append(f"{key.capitalize()}=")
                    result.append(json_to_human_readable(value, prefix + key + "_"))
                else:
                    result.append(f"{key.capitalize()}= {value}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            result.append(f"Item {i + 1}=")
            result.append(json_to_human_readable(item, prefix + "item" + str(i + 1) + "_"))
    else:
        result.append(f"{data}")
    return ";".join(result)

def pick_language(data):
    for key, value in data.items():
        if "language" in key.lower():
            return value

def validate_phone(phone, db):
    user_ref = db.collection('users').document(phone)
    doc = user_ref.get()

    if (doc.exists):
        return True
    else:
        return False

def get_user_data(phone, db):
    user_ref = db.collection('users').document(phone)
    doc = user_ref.get()

    if doc.exists:
        ## Fetch user profile from DB
        user_data = doc.to_dict()
        for k, v in user_data.items():
            if k == 'profile':
                user_profile = v
        
        user_health_profile = get_user_health_profile(user_profile)
        language = pick_language(user_profile)
        workoutplan_ref = db.collection('workoutplan').document(phone)
        workoutplan = ""
        doc1 = workoutplan_ref.get()
        if doc1.exists:
            workoutplan_data = doc1.to_dict()
            for k, v in workoutplan_data.items():
                if k == 'plan':
                    workoutplan = v
        
        chat_hist = db.collection('chats').document(phone)
        doc = chat_hist.get()
        if doc.exists:
            hist_user_bot_conversation = doc.to_dict().get('messages', [])
        
        return {"user_health_profile":user_health_profile
                , "language":language
                , "workoutplan":workoutplan
                , "hist_user_bot_conversation":hist_user_bot_conversation}
    else:
        return "Invalid Phone number. Please try again."

def send_whatsapp(phone_number, message):
    ## If workout plan is created, send Whatsapp message informing the user
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    message = client.messages.create(
        from_='whatsapp:+14155238886',
        body=message,
        to='whatsapp:'+phone_number,
        media='https://example.com/path/image.jpg')

    # resp = MessagingResponse()
    # msg = resp.message()
    # msg.body('this is the response text')
    # msg.media('https://example.com/path/image.jpg')
