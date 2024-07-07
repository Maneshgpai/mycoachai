from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import createProfile as createprofile

db = firestore.Client.from_service_account_json("firestore_key.json")
ist = timezone(timedelta(hours=5, minutes=30))
timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

# phone = input("Provide phone num used to create profile: ")
phone = "+917676105788"
profile_data = {
        "Full Name_pii": "Manesh Pai",
        "Age": "40",
        "Gender": "Male",
        "current_height_in_cm": "181",
        "current_weight_in_kg": "80",
        "Phone_pii": "+917676105788",
        "fitness_goal": "Increase flixibility",
        "workout_types": "Yoga",
        "workout_days": "5",
        "workout_duration": "45-60 minutes",
        "workout_location": "Outdoors",
        "target_weight_in_kg": "60",
        "target_body_fat_percentage": "",
        "current_fitness_level": "",
        "current_workout_equipment": "yoga mat",
        "current_activity_level": "",
        "current_sleep_hours": "7",
        "current_stress_level": "Low",
        "language": "English",
    }

## Delete sample collection
db.collection("users").document(phone).delete()

## Create sample collection
createprofile.save_user_profile(phone, profile_data)
print("Woohoo!!! That's a great first step! You will soon receive Whatsapp message from our agents!")

## Create workout collection
createprofile.create_workoutplan(phone,profile_data)