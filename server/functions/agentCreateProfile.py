from langchain_core.pydantic_v1 import BaseModel
from tavily import TavilyClient
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, HumanMessage
from functions import supportFunc as func
from langchain_openai import ChatOpenAI
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()

model = os.getenv("LLM_MODEL")
db = firestore.Client.from_service_account_json("firestore_key.json")
ist = timezone(timedelta(hours=5, minutes=30))

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
memory = SqliteSaver.from_conn_string(":memory:")
model = ChatOpenAI(model=model, temperature=0)

VISUAL_FORMAT = """You should follow the plan in the pattern given below

Pattern and format of the plan:
Create an engaging and visually appealing table showcasing a sample weekly workout plan. Ensure the overall presentation is eye-catching and motivating. Include the following information for each day:
Day of the Week
Type of Training
Muscle Group Focus
Exercise (Sets x Reps)
Instruction
Reference Video

Example response:
### Workout Plan for Weight Loss - Cardio and Strength Training

#### Week 1 Plan

| **Day** | **Type of Training** | **Exercise Details** |
|---------|----------------------|----------------------|
| 1       | Cardio (Home/Gym)    | [View Exercises](#day-1-cardio-homegym)  |
| 2       | Strength Training    | [View Exercises](#day-2-strength-training-homegym) |
| 3       | Cardio & Strength    | [View Exercises](#day-3-cardio-and-strength-combo-homegym) |

---

### Day 1: Cardio (Home/Gym)

#### Get Your Heart Pumping!

| **Exercise** | **Instruction** | **How to** | **Reference Video** |
|--------------|-----------------|------------|---------------------|
| **Warm-up:** Jumping jacks, high knees | Perform each exercise for 5 minutes | **Jumping Jacks:** 1. Stand with feet together, arms at sides. 2. Jump up, spreading legs shoulder-width apart while raising arms overhead. 3. Jump back to starting position. **High Knees:** 1. Stand with feet hip-width apart. 2. Lift one knee towards chest, then switch legs quickly. | [Warm-up Video](https://www.youtube.com/shorts/lWMw6uppiFc) |
| **Cardio:** Running, cycling, jumping rope | Choose one cardio activity for 20-30 minutes | **Running:** 1. Maintain a steady pace. 2. Focus on breathing. 3. Keep an upright posture. **Cycling:** 1. Adjust the bike seat to a comfortable height. 2. Pedal at a consistent speed. **Jumping Rope:** 1. Hold rope handles at hip height. 2. Jump as the rope swings under feet. | [Cardio Workout](https://www.youtube.com/shorts/GQlebWZpErk) |
| **Cool down:** Stretching | Stretch major muscle groups for 5 minutes | 1. Hold each stretch for 15-30 seconds. 2. Focus on breathing deeply. 3. Stretch all major muscle groups. | [Cool Down Stretches](https://www.youtube.com/shorts/-AkRXKRU0yA) |

---

### Day 2: Strength Training (Home/Gym)

#### Build That Strength!

| **Exercise** | **Instruction** | **How to** | **Reference Video** |
|--------------|-----------------|------------|---------------------|
| **Warm-up:** Dynamic stretches | Perform dynamic stretches for 5 minutes | 1. Perform arm circles. 2. Do leg swings. 3. Rotate your torso. 4. Perform walking lunges. | [Dynamic Warm-up](https://www.youtube.com/watch?v=G6RpZZO2DxY) |
| **Dumbbell Squats** | 3 sets of 12 reps | 1. Stand with feet shoulder-width apart, holding dumbbells at sides. 2. Lower body into a squat position. 3. Keep back straight and knees behind toes. 4. Push through heels to return to starting position. | [Dumbbell Squats](https://www.youtube.com/watch?v=1xMaFs0L3ao) |
| **Push-ups** | 3 sets of 15 reps | 1. Start in a plank position. 2. Lower body until chest nearly touches the floor. 3. Keep body straight from head to heels. 4. Push back up to starting position. | [Push-ups](https://www.youtube.com/watch?v=_l3ySVKYVJ8) |
| **Resistance Band Rows** | 3 sets of 12 reps | 1. Secure the band at a low point. 2. Hold handles and step back to create tension. 3. Pull handles towards your torso, squeezing shoulder blades together. 4. Return to starting position. | [Resistance Band Rows](https://www.youtube.com/watch?v=xPz7m3RQnsI) |
| **Plank** | 3 sets of 30 seconds | 1. Start in a forearm plank position. 2. Keep body in a straight line from head to heels. 3. Engage core muscles. 4. Hold position for the duration. | [Plank Exercise](https://www.youtube.com/watch?v=pSHjTRCQxIw) |
| **Cool down:** Foam rolling | Foam roll major muscle groups for 5 minutes | 1. Use a foam roller on your legs, back, and arms. 2. Roll slowly, pausing on tight spots. 3. Breathe deeply and relax. | [Foam Rolling](https://www.youtube.com/watch?v=8C_ZP3tKnyw) |

---

### Day 3: Cardio and Strength Combo (Home/Gym)

#### Push Your Limits!

| **Exercise** | **Instruction** | **How to** | **Reference Video** |
|--------------|-----------------|------------|---------------------|
| **Warm-up:** Jump rope, arm circles | Perform each exercise for 5 minutes | **Jump Rope:** 1. Hold rope handles at hip height. 2. Jump as the rope swings under feet. **Arm Circles:** 1. Extend arms to sides. 2. Make small circles forward and backward. | [Warm-up Video](https://www.youtube.com/shorts/ZT-Q-Tl8y7I) |
| **HIIT Workout:** Jump Squats | Perform each exercise for 30 seconds, repeat the circuit 3 times | 1. Stand with feet shoulder-width apart. 2. Lower into a squat, then jump explosively. 3. Land softly and repeat. | [HIIT Workout](https://www.youtube.com/shorts/v6I-OtR7GBQ) |
| **Mountain Climbers** | | 1. Start in a plank position. 2. Bring one knee towards chest. 3. Switch legs quickly, alternating knees to chest. |
| **Dumbbell Lunges** | | 1. Stand with feet together, holding dumbbells at sides. 2. Step forward with one leg and lower body until knee is bent at 90 degrees. 3. Push back to starting position and switch legs. |
| **Push-ups** | | 1. Start in a plank position. 2. Lower body until chest nearly touches the floor. 3. Keep body straight from head to heels. 4. Push back up to starting position. |
| **Cool down:** Yoga stretches | Perform yoga stretches for 5 minutes | 1. Perform poses like Child's Pose, Downward Dog, and Forward Bend. 2. Hold each pose for 30 seconds. 3. Focus on deep breathing and relaxation. | [Yoga Cool Down](https://www.youtube.com/watch?v=TD-f4JLPdAI) |

"""

PLAN_PROMPT = """You are an expert health workout plan creator, who knows in detail about every workout possible including Gym, home, outdoor based. These include cardio, yoga, weight training, HIIT, marathon training, swimming, ironman training, aerobics, weight loss trainings, flexibility trainings, medical recuperation trainings and a lot more. You are tasked with writing a high level outline of a workout plan. This plan should be strictly as per the user profile and preferences given. Give an outline of the plan along with any relevant notes or instructions for each section. You are to create plan structure like Exercise name, Reason why this exercise is included, Verbal Instructions on how to do this and Youtube Shorts video link on how to do this. Ensure you only inlude Youtube Shorts video and not any longer video.
"""+VISUAL_FORMAT
    
RESEARCH_PLAN_PROMPT = """You are a health workout researcher charged with providing information that can be used when creating the workout plan. Generate a list of search queries that will gather any relevant information based on the plan provided. Only generate 6 queries max.
"""

WRITER_PROMPT = """You are an expert workout specialist, who knows in detail about every workout possible including Gym, home, outdoor based. These include cardio, yoga, weight training, HIIT, marathon training, swimming, ironman training, aerobics, weight loss trainings, flexibility trainings, medical recuperation trainings and a lot more. You are tasked with writing instructions for each exercise and Youtube Shorts video of how to do each exercise, as per the workout plan. This plan should be strictly as per the user profile and preferences given. Utilize all the information below as needed: \
        ------\
            {content}
            """

REFLECTION_PROMPT = """You are an expert workout trainer who has deep knowledge and experience on every workout plan possible. You are tasked with reviewing a workout plan. Generate critique and recommendations for the user's plan. You should strictly check if the plan and the details suit the user's profile and preferences given. Provide detailed recommendations, including requests for URLs which don't work, any workout item which does not suit the user's profile or preference, risks associated with each plan, incomplete instruction etc. You should also check if there are working and not broken URLs for accompanying Youtube Shorts video or website links. The Youtube Shorts URLs should have content relevant to the item given for."""

RESEARCH_CRITIQUE_PROMPT = """You are a heath workout researcher charged with providing information that can be used when making any requested revisions (as outlined below). Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."""

### Data/State of the agent, i.e the list of messages tracked over time. ###
### Agent state has to persist, i.e state needs to be stored in a DB ###
class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: List[str]
    revision_number: int
    max_revisions: int

class Queries(BaseModel):
    queries: List[str]

### Creating the agent ###
def create_workoutplan(phone_number,user_profile):
    try:
        phone_log_ref = db.collection('log').document(phone_number)

        ### This is Plan node. This node calls LLM to create a high level outline of the workout plan, along with relevant notes ###
        def plan_node(state: AgentState):
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "Entered PLAN NODE...")
                messages = [
                    SystemMessage(content=PLAN_PROMPT), 
                    HumanMessage(content=state['task'])
                ]
                response = model.invoke(messages)
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "Made a plan!", response.content)
                return {"plan": response.content}

        def research_plan_node(state: AgentState):
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "Entered Research NODE...")
                queries = model.with_structured_output(Queries).invoke([
                    SystemMessage(content=RESEARCH_PLAN_PROMPT),
                    HumanMessage(content=state['task'])
                ])
                content = state['content'] or []
                for q in queries.queries:
                    response = tavily.search(query=q, max_results=2)
                    for r in response['results']:
                        content.append(r['content'])
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "Completed Research!")
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "Research queries are:",content)
                return {"content": content}

        def generation_node(state: AgentState):
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "Entered GENERATE node...")
                content = "\n\n".join(state['content'] or [])
                user_message = HumanMessage(
                    content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}")
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "GENERATE: Human message for LLM is:", user_message)
                messages = [
                    SystemMessage(
                        content=WRITER_PROMPT.format(content=content)
                    ),
                    user_message
                    ]
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "GENERATE: Start LLM call+++++++++++++++:")
                response = model.invoke(messages)
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "GENERATE: Finished LLM call+++++++++++++++:")
                
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "GENERATE: Generation Complete!")
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "GENERATE: Revision #", state.get("revision_number", 1) + 1,": Generated draft:",response.content)
                return {
                    "draft": response.content, 
                    "revision_number": state.get("revision_number", 1) + 1
                }

        def reflection_node(state: AgentState):
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "Entered REFLECT node...")
                messages = [
                    SystemMessage(content=REFLECTION_PROMPT), 
                    HumanMessage(content=state['draft'])
                ]
                response = model.invoke(messages)
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "REFLECT: Reflecting Complete!")
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "REFLECT: Reflected content:",response.content)
                return {"critique": response.content}

        # def research_critique_node(state: AgentState):
                # queries = model.with_structured_output(Queries).invoke([
                #     SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
                #     HumanMessage(content=state['critique'])
                # ])
                # content = state['content'] or []
                # for q in queries.queries:
                #     response = tavily.search(query=q, max_results=2)
                #     for r in response['results']:
                #         content.append(r['content'])
                # return {"content": content}
            
        def should_continue(state):
                print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "Entered Conditional Edge. Should continue (Y/N)?...")
                if state["revision_number"] > state["max_revisions"]:
                    print("NO, don't continue!")
                    return END
                print("YES, continue reflecting...")
                return "reflect"

        print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "******** Initialising agent ******** ")
        builder = StateGraph(AgentState)
        builder.add_node("planner", plan_node)
        builder.add_node("generate", generation_node)
        builder.add_node("reflect", reflection_node)
        builder.add_node("research_plan", research_plan_node)
        ## START: Removing critique agent actions, to save cost of querying. This will be helpful when creating more complicated outputs like research papers. ###
        # builder.add_node("research_critique", research_critique_node) ## No need for critique for a health workout plan
        ## END: Removing critique agent actions, to save cost of querying. This will be helpful when creating more complicated outputs like research papers. ###
        builder.set_entry_point("planner")
        builder.add_conditional_edges(
            "generate", 
            should_continue, 
            {END: END, "reflect": "reflect"}
            )
        
        ## START: Removing critique agent actions, to save cost of querying. This will be helpful when creating more complicated outputs like research papers. ###
        # builder.add_edge("planner", "research_plan")
        # builder.add_edge("research_plan", "generate")
        # builder.add_edge("reflect", "research_critique")
        # builder.add_edge("research_critique", "generate")

        builder.add_edge("planner", "research_plan")
        builder.add_edge("research_plan", "generate")
        builder.add_edge("reflect", "generate")
        ## END: Removing critique agent actions, to save cost of querying. This will be helpful when creating more complicated outputs like research papers. ###

        graph = builder.compile(checkpointer=memory)
        print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "******** Agent graph compiled ******** ")

        thread = {"configurable": {"thread_id": phone_number}}
        
        human_message = func.json_to_human_readable(user_profile)
        lang = func.pick_language(user_profile)
        human_message = "Give a workout plan in "+lang+" language strictly considering the user profile and preferences. Plan should strictly consider age, gender, current weight(in kg), current activity level, current fitness level, current workout equipment (if any), current sleep hours (if any), fitness goal (if any) and current stress level. The plan should be exactly as per the workout type selected by user. The plan duration for each day must be achievable within the workout duration given, based on the current fitness level and be possible in the workout locations. If any workout equipment is provided, plan should include these. Plan should also consider other options which are possible without using the current equipment. The details of the various needs of the user are given within three exclamations.!!!"+human_message+"!!!"

        print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), "******** Agent graph executing ******** ")
        for event in graph.stream({
            'task': human_message,
            "max_revisions": 2,
            "revision_number": 1,
        }, thread):
            for key, value in event.items():
                if key == 'generate' and value.get('revision_number') == 3:
                    print(datetime.now(timezone(timedelta(hours=5, minutes=30))),'********* Final response *********')
                    # return value['draft']
                    print(f"{datetime.now(timezone(timedelta(hours=5, minutes=30)))}, Saving the workout plan into DB:{value['draft']}")
                    db.collection('workoutplan').document(phone_number).set({"timestamp": datetime.now(timezone(timedelta(hours=5, minutes=30))),"action":"create_workoutplan","plan":value['draft']})
                    print(f"{datetime.now(timezone(timedelta(hours=5, minutes=30)))}, Saved the workout plan into DB")
                else:
                    print(datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"), f"******** {key} agent response ******** ")
        response = {"status": "Agent created and saved workout plan successfully to DB","timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    
    except Exception as e:
        error = "Error: {}".format(str(e))
        response = {"status": "Error in agent Create Profile","status_cd": 400,"message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}

    ## Logging start ##
    func.createLog(phone_log_ref, response)
    ## Logging stop ##

    try:
        message = 'Hello, Your work profile has been created successfully. You can ask me about anything related to your workout plan.'
        func.send_whatsapp(phone_number, message)
        response = {"status": "Workout plan confirmation sent on Whatsapp","timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    except Exception as e:
        error = "Error: {}".format(str(e))
        response = {"status": "Error in Whatsapp confirmation for Workout plan","status_cd":400,"message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}

    ## Logging start ##
    func.createLog(phone_log_ref, response)
    ## Logging stop ##

    return response

    