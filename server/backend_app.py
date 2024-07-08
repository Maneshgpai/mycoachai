import os
from flask import Flask, jsonify, request, make_response, Response, stream_with_context
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse
import json
import base64
from google.cloud import firestore
from functions import supportFunc as func, agentChat as agentChat, agentCreateProfile as createprofile
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta, timezone
from celery import Celery

load_dotenv(find_dotenv())

db = firestore.Client.from_service_account_json("firestore_key.json")
ist = timezone(timedelta(hours=5, minutes=30))

app = Flask(__name__)
CORS(app)
app.config['CELERY_BROKER_URL'] = os.getenv("CELERY_BROKER_URL")
app.config['CELERY_RESULT_BACKEND'] = os.getenv("CELERY_RESULT_BACKEND")
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def create_workoutplan_async(phone_number,profile_data):
    async_response = createprofile.create_workoutplan(phone_number,profile_data)
    return async_response

@app.route("/api", methods=['GET'])
def home():
    return jsonify({"message": "You have reached an unavailable URL!"})

@app.route("/api/mock_chat", methods=["POST"])
def mock_chat():
    try:
        ### Code for mock Streamlit chat:
        # print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********Entered mock_chat API") ## [user_health_profile, lang, workoutplan]
        data = request.json
        # print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********mock_chat API >> Data for the user is {data}") ## [user_health_profile, lang, workoutplan]

        messages = []
        phone_number = data.get('phone_number')

        if func.validate_phone(phone_number, db):
            latest_user_message = data.get('latest_user_message')
            hist_user_bot_conversation = data.get('hist_user_bot_conversation')
            language = data.get('language')
            workoutplan = data.get('workoutplan')
            user_health_profile = data.get('user_health_profile')
            # print(f"********** Received Streamlit chat message from {phone_number}\n\n latest_user_message {latest_user_message}\n\n language {language}\n\n hist_user_bot_conversation{hist_user_bot_conversation}\n\n workoutplan {workoutplan}\n\n user_health_profile {user_health_profile}\n\n")

            botresponse = ""
            botresponse = agentChat.agent_response(phone_number, latest_user_message, language, hist_user_bot_conversation, workoutplan,user_health_profile)
            status_cd = 200
            response = {"status": "Success","status_cd": status_cd,"message": botresponse}
            log_response = {"message": "MOCK Chat API > Bot responded successfully","bot_message": botresponse,"user_message":latest_user_message, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        else:
            botresponse = f"Hello! I don't find a workout profile for you against phone {phone_number}."
            log_response = {"status": "MOCK Chat API > Error in phone number validation","status_cd":400, "message": botresponse, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    except Exception as e:
        error = "Error: {}".format(str(e))
        status_cd = 400
        log_response = {"status": "Error in MOCK Chat API call","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        response = {"status": "Error","status_cd": status_cd,"message": error}

    # hist_user_bot_conversation.append({"role": "user", "content": latest_user_message, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
    hist_user_bot_conversation.append({"role": "assistant", "content": response, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"source":"mock_chat"})
    chat_ref = db.collection('chats').document(phone_number)
    if not chat_ref.get().exists:
        chat_ref.set({'messages': []})
    chat_ref.update({"messages": firestore.ArrayUnion(hist_user_bot_conversation)})

    ## Logging start ##
    phone_log_ref = db.collection('log').document(phone_number)
    func.createLog(phone_log_ref, log_response)
    ## Logging stop ##

    ### Code for mock Streamlit chat:
    return jsonify(response), status_cd

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********Entered CHAT API")
        # messages = []
        phone_number = request.form.get('From')
        if func.validate_phone(phone_number, db):
            latest_user_message = request.form.get('Body')
            data = func.get_user_data(phone_number, db)
            print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********CHAT API >> Data for the user is {data}")

            hist_user_bot_conversation = data.get('hist_user_bot_conversation')
            language = data.get('language')
            workoutplan = data.get('workoutplan')
            user_health_profile = data.get('user_health_profile')

            botresponse = ""
            botresponse = agentChat.agent_response(phone_number, latest_user_message, language, hist_user_bot_conversation, workoutplan,user_health_profile)
            api_response = {"status": "Success","status_cd":200,"message": botresponse}
            log_response = {"message": "Chat API > Bot responded successfully","bot_message": botresponse,"user_message":latest_user_message, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        else:
            botresponse = f"Hello! I don't find a workout profile for you against phone {phone_number}."
            log_response = {"status": "Chat API > Error in phone number validation","status_cd":400, "message": botresponse, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {"status": "Chat API > Error in Chat API call","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        api_response = {"status": "Error","status_cd":400,"message": error}

    ## Logging start ##
    phone_log_ref = db.collection('log').document(phone_number)
    func.createLog(phone_log_ref, log_response)
    ## Logging stop ##

    hist_user_bot_conversation.append({"role": "user", "content": latest_user_message, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"source":"chat"})
    hist_user_bot_conversation.append({"role": "assistant", "content": api_response, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"source":"chat"})
    chat_ref = db.collection('chats').document(phone_number)
    if not chat_ref.get().exists:
        chat_ref.set({'messages': []})
    chat_ref.update({"messages": firestore.ArrayUnion(hist_user_bot_conversation)})

    chat_response = MessagingResponse()
    chat_response.message(botresponse)

    return str(chat_response)


@app.route("/api/whatsapp_chat", methods=["POST"])
def whatsapp_chat():
    try:
        ## 1. Get phone_number & message from Twilio
        ## 2. Get context from DB (user profile, language, workout_profile)
        ## 3. Pass phone_number & context to agentChat and get one response
        ## 4. Return the response as string to Twilio
        ## 5a. Handle errors & exception within this Flask app
        ## 5b. Save errors & exception into DB
        ## 5c. Save chat conversations into DB

        phone_number = request.form.get('From')
        print(f"Received Whatsapp message from {phone_number}")
        user_data = func.get_user_data(phone_number, db)
        print(f"Data for the user is {user_data}") ## [user_health_profile, lang, workoutplan]

        latest_user_message = request.form.get('Body')

        # botresponse = ""
        # botresponse = agent_response(phone_number, latest_user_message, language, hist_user_bot_conversation, workoutplan,user_health_profile)
        response = MessagingResponse()
        # response.message(botresponse)
        response.message("Hello, this is your personal coach!")

        return str(response)
    except Exception as e:
        error = "Error: {}".format(str(e))
        # print(traceback.format_exc())   

        # db.collection(uid).document(str(datetime.datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S.%f')))\
        #     .set({"timestamp": datetime.datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S.%f')\
        #           ,"source":"paste_content","query_id":query_id,"query":query_text,"error":error})
        return jsonify({"message": error}), 400

@app.route("/api/create_profile", methods=["POST"])
def create_profile():
    try:
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********Entered CREATE_PROFILE API") ## [user_health_profile, lang, workoutplan]
        data = request.json
        phone_number = data.get('phone_number')
        profile_data = data.get('profile_data')
        
        ## Save profile to DB
        db.collection('users').document(phone_number).set({"timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"action":"create_profile","profile":profile_data})

        phone_log_ref = db.collection('log').document(phone_number)
        ## Logging start ##
        resp = {"message": "Saved profile to DB","timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        func.createLog(phone_log_ref, resp)
        ## Logging stop ##

        task = create_workoutplan_async(phone_number,profile_data)

        ## Logging start ##
        resp = {"message": "Backend api >> Workout plan created successfully","timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        func.createLog(phone_log_ref, resp)
        ## Logging stop ##

        # response = {"status": "Triggered profile creation task","status_cd":200,"message": "Profile is being generated. You will recieve a message once this is complete","timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    except Exception as e:
        error = "Error: {}".format(str(e))
        response = {"status": "Error in api create_profile","status_cd":400,"message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        ## Logging start ##
        func.createLog(phone_log_ref, response)
        ## Logging stop ##

    

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000, debug=False) ### For Render
    app.run(debug=True, port=8080) ### For Local host
    # app.run(port=8080) ### For Local host

