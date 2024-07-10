import streamlit as st
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
# from server.functions import agentCreateProfile as agent
import os
from dotenv import load_dotenv
import json
import requests
from PIL import Image

load_dotenv()
db = firestore.Client.from_service_account_json("firestore_key.json")

ist = timezone(timedelta(hours=5, minutes=30))
timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

# Main application
img_logo = 'images/logo_small1.png'
st.set_page_config(page_title="A.I Coach", page_icon=img_logo, layout="centered", initial_sidebar_state="auto", menu_items={
        'Get Help': 'https://www.physikally.com/help',
        'Report a bug': "https://www.physikally.com/feedback",
        'About': "https://www.physikally.com"
    })
st.logo(img_logo)
st.header("Personal Workout Coach")
col1, col2 = st.columns([8,2])
with col1:
    st.write("Create your own personal trainer in just TWO STEPS!")
    st.write(":grey[Step 1. Fill and submit the below form. ] \n\n :grey[Step 2. Wait for the Whatsapp message from your coach] \n\n")
    st.caption(":grey[Don't forget to set the coach's language. We support many Indian languages!]")
    # st.write(":grey[*Select your language in the form below.]")
with col2:
    st.image('images/logo_small1.png')
st.divider()

languages = [
    "English",
    "Hindi",
    "Bengali",
    "Telugu",
    "Marathi",
    "Tamil",
    "Gujarati",
    "Kannada",
    "Odia",
    "Malayalam",
    "Punjabi"
]
# Function to check if user already exists
def user_exists(phone_number):
    user_ref = db.collection('users').document(phone_number)
    return user_ref.get().exists

# Function to save user profile
def save_user_profile(phone_number, profile_data):
    db.collection('users').document(phone_number).set({"timestamp": timestamp,"action":"create_profile","profile":profile_data})
    
# Function to validate mandatory fields
def validate_mandatory_inputs():
    if st.session_state.get("phone") and st.session_state.get("full_name") and st.session_state.get("age") and st.session_state.get("gender") and st.session_state.get("height") and st.session_state.get("weight") and st.session_state.get("fitness_goal") and st.session_state.get("workout_types") and st.session_state.get("workout_days") and st.session_state.get("workout_duration") and st.session_state.get("workout_location"):
        return True
    return False

# @st.experimental_asyncio.to_thread
def create_workoutplan(phone_number,profile_data,whatsapp_optin):
    public_api_url = os.environ['PUBLIC_API_URL']+'/api/create_profile'
    print(f"Create Profile >> Calling agent {public_api_url}")
    response = {}
    response = json.dumps(response)
    try:
        response = requests.post(public_api_url, json={"phone_number": phone_number,"profile_data":profile_data,"whatsapp_optin":whatsapp_optin})
        response.raise_for_status()
        print (response.json().get("message"))
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
    except Exception as e:
        error = "Error: {}".format(str(e))
        st.error(error)

# Function to validate phone number
def validate_phone_number(phone):
    if len(phone) == 10 and phone.isdigit():
        return True
    return False

def show_phone_number():
    col1, col2 = st.columns([3,10])
    with col1:
        ctry_cd = st.text_input("Country Code :red[*]", max_chars=3, value= "+91", key="ctry_cd", label_visibility="visible", disabled=True)
    with col2:
        phone_number = st.text_input("Phone :red[*]", max_chars=10, key="phone", label_visibility="visible")
    # Check if the phone number is valid
    if phone_number:
        if validate_phone_number(phone_number):
            st.success("Phone number is valid")
        else:
            st.error("Phone number must be 10 digits and numeric")

# Function to display basic information (mandatory inputs)
def basic_information():
    st.text_input("Name :red[*]", key="full_name", max_chars=60)
    st.number_input("Age :red[*]", min_value=15, max_value=100, value=None, key="age")
    st.selectbox("Gender :red[*]", ("Female", "Male", "Transgender", "Other", "Prefer not answer"), index=None, key="gender")
    st.number_input("Height (in cm) :red[*]", step=1, value=None, key="height")
    st.number_input("Weight (in kg) :red[*]", min_value=10, max_value=300, step=1, value=None, key="weight")

    st.selectbox("Primary fitness goal :red[*]", ("General fitness", "Lose weight", "Build muscle", "Improve endurance", "Increase flexibility", "Sport-specific training"), index=None,key="fitness_goal")
    st.multiselect("Types of workouts you enjoy :red[*]", ["Cardio", "Strength training", "HIIT", "Yoga", "Running", "Cycling", "Swimming", "Sports"], key="workout_types")
    st.number_input("Days per week you can commit to working out :red[*]", min_value=1, max_value=7, value=None, key="workout_days")
    st.selectbox("Time per workout session :red[*]", ("15-30 minutes", "30-45 minutes", "45-60 minutes", "More than 60 minutes"), index=None, key="workout_duration")
    st.multiselect("Preferred workout location :red[*]", ["Home", "Gym", "Outdoors"], key="workout_location")

    st.selectbox("Select the language for the coach :red[*]",options=languages, key="language")

# Function to display optional fields
def additional_information():
    with st.expander("Additional Information (Optional)"):
        # Health and Fitness Goals Tab
        st.text_input("Specific target for weight", key="target_weight_in_kg")
        st.text_input("Specific target for body fat percentage", key="body_fat_percentage_%")
        st.selectbox("Current fitness level", ("Beginner", "Intermediate", "Advanced"), index=None, key="fitness_level")

        # Exercise Preferences and History Tab
        st.text_input("Equipment you have access to", key="workout_equipment")

        # Health and Medical History Tab
        # st.radio("Existing medical conditions or injuries", ("Yes", "No"), key="medical_conditions")
        # if st.session_state.get("medical_conditions") == "Yes":
        #     st.text_input("Please specify your medical conditions or injuries", key="medical_conditions_details")
        # st.radio("Currently taking any medication that might affect your exercise routine", ("Yes", "No"), key="medication")
        # if st.session_state.get("medication") == "Yes":
        #     st.text_input("Please specify your medication", key="medication_details")
        # st.text_input("Allergies or dietary restrictions (optional)", key="allergies")

        # Lifestyle and Habits Tab
        st.selectbox("Typical daily activity level",("Sedentary", "Lightly active", "Moderately active", "Very active", "Super active"), index=None, key="activity_level")
        st.selectbox("Hours of sleep per night", ("Less than 5 hours", "5-6 hours", "6-7 hours", "7-8 hours", "More than 8 hours"), index=None, key="sleep_hours")
        st.selectbox("Current stress level",("Low", "Moderate", "High", "Very high"), index=None, key="stress_level")

        # Nutrition and Diet Tab
        # st.radio("Specific diet plan followed", 
        #          ("No specific diet", "Vegetarian", "Vegan", "Keto", "Paleo", "Mediterranean", "Other"), key="diet_plan")
        # st.number_input("Meals and snacks per day", min_value=1, key="meals_per_day")
        # st.radio("Take any supplements", ("Yes", "No"), key="supplements")
        # if st.session_state.get("supplements") == "Yes":
        #     st.text_input("Please specify your supplements", key="supplements_details")

        # Motivations and Preferences Tab
        # st.multiselect("What motivates you to stay fit?", 
        #                ["Health", "Appearance", "Performance", "Other"], key="motivation")
        # st.radio("Prefer working out alone or with a group", 
        #          ("Alone", "Group"), key="workout_preference")
        # st.radio("Would you like a personalized meal plan?", ("Yes", "No"), key="meal_plan")
        # st.radio("Preferred type of coaching", 
        #          ("Motivational", "Instructional", "Supportive", "Other"), key="coaching_preference")

# Function to display optional fields
def get_whatsapp_optin():
    st.radio("I agree to receive WhatsApp messages from Datacorp Llc (legal owner of www.physikally.com)", ("Yes", "No"), key="whatsapp_optin", help="We will NEVER send any messages soliciting or advertising services. You can chat with your personal coach only on Whatsapp. And we need your consent to start this conversation. You can OPT OUT of this by Replying STOP to the Whatsapp number at any time.")


st.subheader("Create Your Profile")
show_phone_number()
with st.form("form_profile", clear_on_submit=False, border=False):
    basic_information()
    additional_information()
    get_whatsapp_optin()    
    submitted = st.form_submit_button("Submit")

# col1, col2, col3 = st.columns([1,1,1])
# with col1:
#     st.empty()
# with col2:
#     st.subheader("Create Your Profile")
#     show_phone_number()
#     with st.form("form_profile", clear_on_submit=False, border=False):
#         basic_information()
#         additional_information()
#         get_whatsapp_optin()    
#         submitted = st.form_submit_button("Submit")
# with col3:
#     st.empty()

# Button to submit the form
if submitted:
    if st.session_state.get("whatsapp_optin") == "Yes":
        if validate_mandatory_inputs():
            phone_number = st.session_state.get("ctry_cd") + st.session_state.get("phone")
            phone_log_ref = db.collection('log').document(phone_number)
            if phone_number:
                if user_exists(phone_number):
                    # print("log 3:",datetime.datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S.%f'))
                    st.warning("A profile with this phone number already exists.")
                    # print("log 4:",datetime.datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S.%f'))
                else:
                    profile_data = {
                        "Full Name_pii": st.session_state.get("full_name"),
                        "Age": st.session_state.get("age"),
                        "Gender": st.session_state.get("gender"),
                        "current_height_in_cm": st.session_state.get("height"),
                        "current_weight_in_kg": st.session_state.get("weight"),
                        "Phone_pii": st.session_state.get("ctry_cd") + st.session_state.get("phone"),
                        "fitness_goal": st.session_state.get("fitness_goal"),
                        "workout_types": st.session_state.get("workout_types"),
                        "workout_days": st.session_state.get("workout_days"),
                        "workout_duration": st.session_state.get("workout_duration"),
                        "workout_location": st.session_state.get("workout_location"),
                        "target_weight_in_kg": st.session_state.get("target_weight_in_kg"),
                        "target_body_fat_percentage": st.session_state.get("body_fat_percentage_%"),
                        "current_fitness_level": st.session_state.get("fitness_level"),
                        "current_workout_equipment": st.session_state.get("workout_equipment"),
                        "current_activity_level": st.session_state.get("activity_level"),
                        "current_sleep_hours": st.session_state.get("sleep_hours"),
                        "current_stress_level": st.session_state.get("stress_level"),
                        "language": st.session_state.get("language"),
                    }
                    # print("log 5:",datetime.datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S.%f'))
                    #save_user_profile(phone_number, profile_data)
                    response = {"status": "Saved profile to DB","status_cd":200,"message": "Saved profile to DB","timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
                    st.success("Woohoo!!! That's a great first step! You can go ahead and close this window. You will soon receive a Whatsapp message from our agents!")
                    create_workoutplan(phone_number,profile_data,st.session_state.get("whatsapp_optin"))

            else:
                st.error("Phone number is mandatory for profile creation.")
        else:
            st.error("Please fill out all mandatory fields.")
    else:
        st.error("Consent is required to receive WhatsApp messages from your coach.")