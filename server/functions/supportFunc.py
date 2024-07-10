from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from google.cloud import firestore

load_dotenv()

ist = timezone(timedelta(hours=5, minutes=30))
db = firestore.Client.from_service_account_json("firestore_key.json")


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

def create_first_chat_collection(phone_number, db):
    chat_ref = db.collection('chats').document(phone_number)
    if not chat_ref.get().exists:
        chat_ref.set({'messages': [], "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})

def validate_phone(phone, db):
    user_ref = db.collection('users').document(phone)
    doc = user_ref.get()
    print(f"validate_phone >> doc:{doc.to_dict()}, phone:{phone}")
    print()
    if (doc.exists):
        return user_ref
    else:
        return False

def get_user_data(phone, db, user_data):
    # user_ref = db.collection('users').document(phone)
    doc = user_data.get()

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
        
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********CHAT API >> get_user_data() >> workoutplan:{workoutplan}")

        chat_hist = db.collection('chats').document(phone)
        doc = chat_hist.get()
        if doc.exists:
            hist_user_bot_conversation = doc.to_dict().get('messages', [])
        else:
            create_first_chat_collection(phone, db)
            hist_user_bot_conversation = []
        
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********CHAT API >> End og get_user_data()")
        return {"user_health_profile":user_health_profile
                , "language":language
                , "workoutplan":workoutplan
                , "hist_user_bot_conversation":hist_user_bot_conversation}
    else:
        print("get_user_data >> NO Doc does not exists")
        return "Invalid Phone number. Please try again."

def send_whatsapp(phone_number, message):
    acct_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_ID")
    content_sid = os.getenv("TWILIO_TEMPLATE_CONTENT_SID_ENGLISH")
    to_whatsapp_number = 'whatsapp:'+phone_number
    # content_variables = {
    #     '1': 'John Doe',  # Example placeholder value
    #     '2': 'Your order has been shipped!'  # Example placeholder value
    # }
    client = Client(acct_sid, auth_token)
    message = client.messages.create(
        messaging_service_sid=messaging_service_sid,
        body=message,
        to=to_whatsapp_number,
        content_sid=content_sid,
        # content_variables=content_variables
    )

def createLog(phone_log_ref, response):
    phone_log_ref.collection("session_"+datetime.now(ist).strftime('%Y-%m-%d')).document(str(datetime.now(ist))).set(response)
