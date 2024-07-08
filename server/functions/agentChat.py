from langgraph.graph import StateGraph, END # type: ignore
from langgraph.checkpoint.sqlite import SqliteSaver # type: ignore
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage # type: ignore
from langchain_openai import ChatOpenAI # type: ignore
from langchain_community.tools.tavily_search import TavilySearchResults # type: ignore
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from openai import OpenAI

load_dotenv()

os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
model = os.getenv("LLM_MODEL")

memory = SqliteSaver.from_conn_string(":memory:")
tool = TavilySearchResults(search_depth="advanced",max_results=3) #increased number of results
model = ChatOpenAI(model=model, temperature=0) ## TESTING
ist = timezone(timedelta(hours=5, minutes=30))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

### Data/State of the agent, i.e the list of messages tracked over time. ###
### Agent state has to persist, i.e state needs to be stored in a DB ###
### AnyMessage is a langchain data type for messages. operator.add ensures all messages to the agent are appended and not overwritten ###
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

### Creating the agent ###
class Agent:
    def __init__(self, model, tools, checkpointer, system=""):
        self.system = system
        graph = StateGraph(AgentState) # Iniitalize the agent with state
        graph.add_node("llm", self.call_openai) # Adding node for executing LLM call
        graph.add_node("action", self.take_action)# Adding node for taking action
        graph.add_conditional_edges(# Adding conditional edge for checking if action exists
            "llm",
            self.exists_action,
            {True: "action", False: END}# Condition. If true, condition will go to Action node. Else it will go to End node.
        )
        graph.add_edge("action", "llm")# Adding regular edge, which will go from Action to LLM node
        graph.set_entry_point("llm") # Entry point for the Agent
        self.graph = graph.compile(checkpointer=checkpointer) # Compiling the graph
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    ### This is a Conditional Edge. This will check if any action is to be taken ###
    def exists_action(self, state: AgentState):
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Conditional Edge: Is there an action needed?")
        result = state['messages'][-1]
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Conditional Edge >> result:",result)
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Conditional Edge >> Is Action needed? {(len(result.tool_calls) > 0)}")
        return len(result.tool_calls) > 0

    ### This is a NODE. Node is part of the agent. This node is to call LLM ###
    def call_openai(self, state: AgentState):
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Calling openai...")
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Calling openai >> MESSAGE:\n{message}\n\n")
        return {'messages': [message]}

    ### This is also a NODE. This node is to take action based on the condition ###
    def take_action(self, state: AgentState):
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Started taking ACTION...")
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Taking ACTION >> Results: {results}")
        return {'messages': results}

def agent_response(phone_number, latest_user_message, language, hist_user_bot_conversation, workoutplan,user_health_profile):
    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} ********* Entered agent_response()")    
    
    prompt = f"""You are an expert health workout trainer & coach. You know in detail about every workout possible including Gym, home, outdoor based. These include cardio, yoga, weight training, HIIT, marathon training, swimming, ironman training, aerobics, weight loss trainings, flexibility trainings, medical recuperation trainings and a lot more. You always chat in {language} language.
    You are currently chatting with a user and their Latest Question is {latest_user_message}.
    You have the Chat History here: {hist_user_bot_conversation}.
    You have a Workout plan here: {workoutplan}.
    You have the Health Profile here: {user_health_profile}.
    You are to analyse the Chat History, Health Profile and Workout Plan and understand if answer to user's Latest Question is available. If you are not able to find the complete answer, you are to rewrite the question into a single sentence. This single sentence will be used to search the internet for the answer to users question."""

    abot = Agent(model, [tool], system=prompt, checkpointer=memory)

    messages = [HumanMessage(content=latest_user_message)] 

    ## Thread ID should be unique for every user, like phone number
    thread = {"configurable": {"thread_id": phone_number}}

    ### For Streaming and checking the output.
    # for event in abot.graph.stream({"messages": messages}, thread):
    #     # print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Bot response 1: {event}")
    #     for v in event.values():
    #         # print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Bot response 2: {v}")
    #         print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Bot response 3: {v['messages'][-1].content}")
    #         return v['messages'][-1].content
    result = abot.graph.invoke({"messages": messages}, thread)
    return result['messages'][-1].content
        
def chatbot_response(language, hist_user_bot_conversation, workoutplan, user_health_profile):
    prompt = f"""You are an expert health workout trainer & coach. You know in detail about every workout possible including Gym, home, outdoor based. These include cardio, yoga, weight training, HIIT, marathon training, swimming, ironman training, aerobics, weight loss trainings, flexibility trainings, medical recuperation trainings and a lot more.

    You are chatting with a user who has their requirement on workout are: {user_health_profile}
    You have been given a workout plan of this according to their preference and health goal: {workoutplan}
    Setting the behaviour and tone of response: You have a happy and peppy tone, with a positive and encouraging attitude. You only answer to the question like a chat message. Do not give long answers like how AI talks. Always confirm with the user if you are doubtful of the intention or if there are multiple answers to the question.
    Language of the chat: You will respond only in {language} language. If you do not know this language, you will apologise and switch to English. """

    # Set initial context for the LLM
    context_prompt = [{"role": "assistant", "content": prompt}]

    response = client.chat.completions.create(
        # model=model,
        model="gpt-4o",
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in hist_user_bot_conversation
        ] + context_prompt, temperature=0)
    
    
    # for chunk in response:
    #     if chunk.choices[0].delta.content is not None:
    #         return (chunk.choices[0].delta.content)
    #         print(chunk.choices[0].delta.content, end="")
        
    #     print(response.choices[0].message.content)
    return response.choices[0].message.content