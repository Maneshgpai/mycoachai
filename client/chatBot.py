from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import streamlit as st
import hmac
import os
from dotenv import load_dotenv
import json
import requests

load_dotenv()
db = firestore.Client.from_service_account_json("firestore_key.json")
ist = timezone(timedelta(hours=5, minutes=30))
st.session_state.status = st.session_state.get("status", "unverified")

def check_password():
    if hmac.compare_digest(st.session_state.password, os.getenv("LOGIN_PASSWORD")):
        st.session_state.status = "verified"
    else:
        st.session_state.status = "incorrect"
    st.session_state.password = ""

## Function to get and display voice_id input
def login_prompt():
    st.text_input("Enter password:", key="password", type="password", on_change=check_password)
    if st.session_state.status == "incorrect":
        st.warning("Incorrect password. Please try again.")

def logout():
    st.session_state.status = "unverified"
    st.session_state["user_profile"] = ""

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

## Function to create a new chat document if it doesn't exist
# def create_chat(phone_number):
#     chat_ref = db.collection('chats').document(phone_number)
#     if not chat_ref.get().exists:
#         chat_ref.set({'messages': [], "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})

## Function for bot response
def get_agent_response(phone_number, latest_user_message, language, hist_user_bot_conversation, workoutplan,user_health_profile):
    public_api_url = os.environ['PUBLIC_API_URL']+'/api/mock_chat'
    print(f"Mock chat >> Calling agent {public_api_url}")
    response = {}
    response = json.dumps(response)
    try:
        response = requests.post(public_api_url
        , json={"phone_number": phone_number,
                "latest_user_message": latest_user_message,
                "language": language,
                "hist_user_bot_conversation":hist_user_bot_conversation,
                "workoutplan":workoutplan,
                "user_health_profile":user_health_profile})
        response.raise_for_status()
        print(f"Mock chat >> Agent response: Status code {response.status_code}. Message:{response.json().get('message')}\n")
        return (response.json().get("message"))
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
    except Exception as e:
        error = "Error: {}".format(str(e))
        st.error(error)

# def get_chatbot_response(language, hist_user_bot_conversation, workoutplan, user_health_profile):
#     response = agent.chatbot_response(language, hist_user_bot_conversation, workoutplan, user_health_profile)
#     return response

## Function to get chat messages from Firebase
def get_chat_messages(phone_number):
    chat_ref = db.collection('chats').document(phone_number)
    doc = chat_ref.get()
    if doc.exists:
        return doc.to_dict().get('messages', [])
    else:
        # create_chat(phone_number)
        return []

## Function to save chat history to Firebase
# def save_chat_history(phone_number, messages):
#     chat_ref = db.collection('chats').document(phone_number)
#     ist = timezone(timedelta(hours=5, minutes=30))
#     timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
#     chat_ref.update({"messages": firestore.ArrayUnion(messages)})

def set_user_session(phone):
    user_ref = db.collection('users').document(phone)
    doc = user_ref.get()

    if doc.exists:
        if "phone_number" not in st.session_state:
            st.session_state["phone_number"] = phone

        ## Fetch user profile from DB
        user_data = doc.to_dict()
        for k, v in user_data.items():
            if k == 'profile':
                user_profile = v
        if "user_profile" not in st.session_state:
            st.session_state["user_profile"] = user_profile
        
        ## Fetch user's health requirement & specs
        user_health_profile = get_user_health_profile(user_profile)
        if "user_health_profile" not in st.session_state:
            st.session_state["user_health_profile"] = user_health_profile
        
        ## Fetch user's preferred language from DB
        lang = pick_language(user_profile)
        if "language" not in st.session_state:
            st.session_state["language"] = lang
        
        # Fetch workout plan from DB. Not present for first time user, who has not created any plan
        workoutplan_ref = db.collection('workoutplan').document(st.session_state["phone_number"])
        workoutplan = ""
        doc1 = workoutplan_ref.get()
        if doc1.exists:
            workoutplan_data = doc1.to_dict()
            for k, v in workoutplan_data.items():
                if k == 'plan':
                    workoutplan = v
        if "workoutplan" not in st.session_state:
            st.session_state["workoutplan"] = workoutplan
        
        messages = get_chat_messages(phone)
        if "messages" not in st.session_state:
            st.session_state.messages = messages
    else:
        st.error("Invalid Phone number. Please try again.")

## Function to get user data by phone number
def get_phone_number():
    phone = st.text_input("Phone :red[*]", max_chars=10, label_visibility="visible")  
    submit = st.button("Submit")
    if submit:
        set_user_session(phone)
        ## Rerun the script to load the chat interface
        st.rerun()

# Function to display the chat interface
def chat_interface():
    st.subheader("mycoach.ai")

    ## Display the Phone number as un-editable
    st.text_input("Details for ", value=st.session_state["phone_number"], disabled=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    print(f"Mock chat >> Calling agent {st.session_state.messages}")

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input for new message    
    if prompt := st.chat_input(""):
        st.session_state.messages.append({"role": "user", "content": prompt, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"source":"mock_chat"})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("ai"):
            response = get_agent_response(st.session_state["phone_number"], prompt, st.session_state["language"], st.session_state.messages,st.session_state["workoutplan"],st.session_state['user_health_profile'])
            # response = get_chatbot_response(st.session_state["language"], st.session_state.messages,st.session_state["workoutplan"],st.session_state['user_health_profile'])
            st.write(response)
            
        st.session_state.messages.append({"role": "assistant", "content": response, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"source":"mock_chat"})

# Main function to control the flow
def main():
    if st.session_state.status != "verified":
        login_prompt()
        st.stop()
    else:
        if "user_profile" in st.session_state and st.session_state["user_profile"] != "":
            chat_interface()
        else:
            get_phone_number()

if __name__ == "__main__":
    main()
