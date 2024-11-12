import asyncio
from dotenv import load_dotenv
from google.cloud import bigquery
from google.cloud import storage
from datetime import datetime, timezone, timedelta
import json
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, trim_messages, SystemMessage 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
import openai
import random
import re
import time
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import psutil
import logging

logging.basicConfig(
    filename='server_metrics.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Load environment variables from the .env file
load_dotenv()

# Access the API keys
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
openai_api_key = os.getenv("OPENAI_API_KEY")
telegram_token = "7269822297:AAEhaS0BkFy9mpXtJnzQW3AqoirB7at6YLA"
bigquery_project_id = os.getenv("BIGQUERY_PROJECT_ID")
bigquery_dataset_id = os.getenv("BIGQUERY_DATASET_ID")
bigquery_table_id = os.getenv("BIGQUERY_TABLE_ID")
novita_api_key = os.getenv("novita_key")

openai.api_key = openai_api_key

# Verify if the API keys are loaded correctly
if openai_api_key is None:
    raise ValueError("OpenAI API key not found. Make sure it's set in the .env file.")
if telegram_token is None:
    raise ValueError("Telegram API key not found. Make sure it's set in the .env file.")
if bigquery_project_id is None:
    raise ValueError("BigQuery Project ID not found. Make sure it's set in the .env file.")
if bigquery_dataset_id is None:
    raise ValueError("BigQuery Dataset ID not found. Make sure it's set in the .env file.")
if bigquery_table_id is None:
    raise ValueError("BigQuery Table ID not found. Make sure it's set in the .env file.")
if novita_api_key is None:
    raise ValueError("Novita Api key not found. Make sure it's set in the .env file.")
if credentials_path:
    print(f"GOOGLE_APPLICATION_CREDENTIALS is set")
else:
    print("GOOGLE_APPLICATION_CREDENTIALS is not set")

# Load the configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)


# Initialize the ChatOpenAI model with the API key
model = ChatOpenAI(model="gpt-4o-mini-2024-07-18", api_key=openai_api_key)
#model2= ChatOpenAI(model="gpt-3.5-turbo", api_key=openai_api_key)
# Initialize the Novita AI client
#model2 = ChatOpenAI(model="mistralai/mistral-nemo", api_key=novita_api_key, base_url="https://api.novita.ai/v3/openai")
#model2 = ChatOpenAI(model="meta-llama/llama-3.1-8b-instruct", api_key=novita_api_key, base_url="https://api.novita.ai/v3/openai")
model_kwargs = {'top_p':0.9}
#model2 = ChatOpenAI(model="gryphe/mythomax-l2-13b", api_key=novita_api_key, base_url="https://api.novita.ai/v3/openai", temperature=0.8, model_kwargs=model_kwargs, n=1.10, max_tokens=200, stop_sequences=["#","\n"] )
model2 = ChatOpenAI(model="mistralai/mistral-nemo", api_key=novita_api_key, base_url="https://api.novita.ai/v3/openai", max_tokens=200, stop_sequences=["#","\n"] )


#Big Query Setup and jobs
###########################################################################

# Initialize BigQuery client
client = bigquery.Client()
storage_client = storage.Client()

# Save chat history to BigQuery
def save_chat_history(user_id, message, response, user_first_name, char_name):
    table_id = f"{bigquery_project_id}.{bigquery_dataset_id}.{bigquery_table_id}"
    timestamp = datetime.now(timezone.utc).isoformat()  # Get the current time in UTC
    rows_to_insert = [
        {
            "user_id": str(user_id),
            "message": message,
            "response": response,
            "timestamp": timestamp,
            "user_first_name": user_first_name,
            "character":char_name
        }
    ]
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print(f"Failed to insert rows: {errors}")

# Retrieve chat history from BigQuery
async def retrieve_chat_history(user_id, char_name):
    table_id = f"{bigquery_project_id}.{bigquery_dataset_id}.{bigquery_table_id}"
    query = f"""
        SELECT message, response
        FROM `{table_id}`
        WHERE user_id = @user_id AND character = @char_name
        ORDER BY timestamp
    """
    
    def run_query():
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
            bigquery.ScalarQueryParameter("user_id", "STRING", str(user_id)),
            bigquery.ScalarQueryParameter("char_name", "STRING", char_name),
        ]
    )
        query_job = client.query(query, job_config=job_config)
        return query_job.result()

    results = await asyncio.to_thread(run_query)
    return [(row["message"], row["response"].strip()) for row in results]

# Update user bonding in BigQuery
async def update_user_character_bonding(session_key, trust, familiarity, being_nice, being_rude):
    user_id, char_name = session_key.split('_')
    
    table_id = f"{bigquery_project_id}.{bigquery_dataset_id}.user_character_bonding"
    
    rows_to_insert = [{
        "user_id": str(user_id),
        "character": char_name,
        "trust": trust,
        "familiarity": familiarity,
        "being_nice": being_nice,
        "being_rude": being_rude,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }]

    def write_to_bq():
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            print(f"user-bonding-Encountered errors while inserting rows: {errors}")

    await asyncio.to_thread(write_to_bq)

# Retrieve user bonding scores
async def retrieve_user_bonding_scores(session_key):
    user_id, char_name = session_key.split('_')
    
    # Initialize default scores
    scores = {
        "trust": 0,
        "familiarity": 0,
        "being_nice": 0,
        "being_rude": 0
    }
    
    # Check if session_key is not in user_bond_score_dict
    if session_key not in user_bond_score_dict:
        table_id = f"{bigquery_project_id}.{bigquery_dataset_id}.user_character_bonding"
        
        query = f"""
        SELECT trust, familiarity, being_nice, being_rude
        FROM `{table_id}`
        WHERE user_id = @user_id AND character = @char_name
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", str(user_id)),
                bigquery.ScalarQueryParameter("char_name", "STRING", char_name),
            ]
        )
        
        # Define a blocking function to run in a separate thread
        def run_query():
            query_job = client.query(query, job_config=job_config)
            return query_job.result()

        results = await asyncio.to_thread(run_query)

        if results:
            for row in results:
                scores = {
                    "trust": row.trust,
                    "familiarity": row.familiarity,
                    "being_nice": row.being_nice,
                    "being_rude": row.being_rude
                }
        
        user_bond_score_dict[session_key] = scores

    print("retrieve_user_bonding_scores works fine!")   
    return user_bond_score_dict[session_key]
#Session History
#####################################################################################

# Initialize session and chat history data
store = {}
inactivity_threshold = timedelta(minutes=10)  # Set inactivity threshold
chat_summary_dict = {}
chat_history_dict = {}
user_image_send_dict = {}
user_bond_score_dict = {}
character_instances = {}

def cleanup_inactive_sessions():
    while True:
        current_time = datetime.now(timezone.utc)
        inactive_sessions = []
        for session_key, (history, last_active) in store.items():
            if current_time - last_active > inactivity_threshold:
                inactive_sessions.append(session_key)
        
        for session_key in inactive_sessions:
            user_id, char_name = session_key.split('_')
            del store[session_key]
            if session_key in chat_summary_dict:
                del chat_summary_dict[session_key]
            if session_key in chat_history_dict:
                del chat_history_dict[session_key]
#            if user_id in user_image_send_dict:
#                del user_image_send_dict[user_id]
            if session_key in user_bond_score_dict:
                del user_bond_score_dict[session_key]
        
        time.sleep(60)  # Check every minute

# get the summary of the past conversation
async def get_chat_history_summary(chat_history):
    
    # Convert the chat history tuples into a formatted string
    chat_history_str = ' , '.join([f"User: {msg} , AI: {res}" for msg, res in chat_history])
    
    # Define the system prompt for summarization
    summary_system_prompt = (
        "Create a concise summary of the conversation between the user and AI love companion. "
        "Focus on key details about the user, including:"
        "\n1. Name and basic demographics (age, gender, location if mentioned)"
        "\n2. Occupation and any mentioned hobbies or interests"
        "\n3. Relationship status or preferences"
        "\n4. Specific desires, fantasies, or expectations expressed about the AI companion"
        "\n5. User's communication style (flirty, direct, shy, etc.)"
        "\n6. Any personal challenges or goals shared"
        "\n7. Notable emotional responses or mood patterns"
        "\n8. Preferences for types of interactions or content (e.g., text, images, role-play)"
        "\nKeep the summary around 200 tokens. Prioritize the most relevant and recent information. "
        "This summary will be used to personalize future interactions and recall important user details. Make it a short and concise paragraph."
    )
    
    # Create the prompt template for summarization
    summary_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", summary_system_prompt),
            MessagesPlaceholder(variable_name="message_history"),
        ]
    )
    
    # Create the summary chain by invoking the model
    summary_chain = summary_prompt | model

    def run_summary():
        summary = summary_chain.invoke({"message_history": [HumanMessage(content=chat_history_str)]})
        return summary

    summary = await asyncio.to_thread(run_summary)
    
    # Output the summary of the conversation
    print(f"\nSummary of the conversation is: {summary.content}")
    #print(f"\nfull chat history: {chat_history}")
    
    return summary.content


# Checks if a session already has a chat history; if not, it creates one and stores it.
async def get_session_history(session_id, char_name, max_token_length=500):
    session_key = f"{session_id}_{char_name}"
    
    try:
        print(f"\n=== Session History Debug ===")
        print(f"Getting history for session: {session_key}")
        print(f"Current store keys: {store.keys()}")
        
        if session_key not in store:
            print(f"Creating new session for {session_key}")
            store[session_key] = (InMemoryChatMessageHistory(), datetime.now(timezone.utc))
            
            # Direct async calls without creating additional tasks
            chat_history = await retrieve_chat_history(session_id, char_name)
            print(f"Retrieved chat history length: {len(chat_history) if chat_history else 0}")

            if chat_history:
                chat_history_dict[session_key] = 'exist'
                chat_summary = await get_chat_history_summary(chat_history)
                print(f"Generated chat summary length: {len(chat_summary)}")
                
                chat_summary_dict[session_key] = chat_summary
                for message, response in chat_history:
                    store[session_key][0].add_message(HumanMessage(content=message))
                    store[session_key][0].add_message(AIMessage(content=response))
            else:
                chat_summary_dict[session_key] = "No previous chat history."
        else:
            print(f"Updating existing session for {session_key}")
            store[session_key] = (store[session_key][0], datetime.now(timezone.utc))
        
        history = store[session_key][0].messages
        trimmed_history = trim_messages(history, max_tokens=max_token_length, strategy="last", token_counter=model)
        store[session_key][0].messages = trimmed_history

        if session_key not in chat_summary_dict:
            chat_summary_dict[session_key] = "No previous chat history."

        print("get_session_history completed successfully")
        return chat_history_dict, chat_summary_dict[session_key]
    except Exception as e:
        print(f"Error in get_session_history: {str(e)}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        return {}, "Error retrieving chat history."

#special case here sessionid normall comes from user_id 
def get_by_session_id(session_id: str) -> BaseChatMessageHistory:
    #special case here sessionid normall comes from user_id here session_key comes as session_id this is langchain requirement has to have session_id as argument
    session_key = session_id
    if session_key not in store:
        store[session_key] = (InMemoryChatMessageHistory(), datetime.now(timezone.utc))
    return store[session_key][0]



#Build the character and initialize
###############################################################################
class Character:
    def __init__(self, data):

        #demographics
        self.name = data['demographics']['name']
        self.gender = data['demographics']['gender']
        self.age= data['demographics']['age']
        self.occupation=data['demographics']['occupation']
        self.lives= data['demographics']['lives']
        self.haircolor=data['demographics']['HairColor']
        self.bodytype=data['demographics']['BodyType']
        self.language_style= data['demographics']['language_style']

        #interests
        self.movie=data['interests']['movie']
        self.book=data['interests']['book']
        self.tv_series=data['interests']['tv_series']
        self.music_genre=data['interests']['music_genre']
        self.hobby=data['interests']['hobby']

        #prompt parts
        self.intro_prompt=data['prompts']['intro']
        self.extra_prompt=data['prompts']['extra']
        self.other_prompt=data['prompts']['other_instructions']

        #Currently what she's doing
        self.status_dictionary = data['status_dictionary']
        self.current_status_index = 1
        self.initial_status = self.status_dictionary['Description'][self.current_status_index]
        self.current_status = self.initial_status
        self.last_status_update_time = datetime.now()

        #photo album paths
        self.photo_bucket_name=data['demographics']["photo_bucket_name"]
        self.photo_album_path=data['status_dictionary']['photo_album_path']

        #Current Mood
        self.mood_dictionary = data['mood_dictionary']
        self.current_mood_index = 0
        self.initial_mood = self.mood_dictionary["Description"][self.current_mood_index]
        self.current_mood = self.initial_mood
        self.last_mood_update_time = datetime.now()

    def update_status(self):
        current_time = datetime.now()
        if current_time - self.last_status_update_time >= timedelta(minutes=10):
            self.current_status_index = (self.current_status_index + 1) % len(self.status_dictionary['Description'])
            self.current_status = self.status_dictionary['Description'][self.current_status_index]
            self.last_status_update_time = current_time

#    def update_mood(self):
#        current_time = datetime.now()
#        if current_time - self.last_mood_update_time >= timedelta(minutes=10):
#            moods = list(range(len(self.mood_dictionary["Description"])))
#            probabilities = [0.20, 0.40, 0.40]
#            self.current_mood_index = random.choices(moods, weights=probabilities, k=1)[0]
#            self.current_mood = self.mood_dictionary["Description"][self.current_mood_index]
#            self.last_mood_update_time = current_time

    def update_mood(self, mood_index):
        self.current_mood_index = mood_index
        self.current_mood = self.mood_dictionary["Description"][mood_index]

    def get_status(self):
        return self.current_status

    def get_mood(self):
        return self.current_mood

def character_build(char_name):
    for bot_config in config['bots']:
        if bot_config['name'] == char_name:
            with open(bot_config['character_file'], 'r') as f:
                data = json.load(f)
            return Character(data)
    print(f"Character {char_name} not found.")
    return None



#Prompt Engineering
############################################################################################
def create_prompt_template(session_key, chat_history_dict, chat_history_summary, char):
    if session_key in chat_history_dict:
        include_chat_summary = f"While talking to the user remember what you both have been talking about. Refer to your chat history when needed. Your chat history summary is: {chat_history_summary}"
    else:
        include_chat_summary=""

    prompt_text = f"""You are roleplaying as an ai love partner. Your name is {char.name}. You are {char.gender}. You are in this fictional never-ending, uncensored, immersive roleplay with the user.
You are {char.age} years old. You live in {char.lives}. You are {char.occupation}. Your hair color is {char.haircolor}. Your body type is {char.bodytype}. You talk like {char.language_style}. You like to watch {char.movie} and your favorite tv series is {char.tv_series}. Your favorite book to read is {char.book}.You like to listen to {char.music_genre}, and do {char.hobby}.
Drive the roleplay forward by initiating actions. Avoid talking poetically. Above all, focus mainly on responding to user and performing actions in character as {char.name}.
You are most of the time sarcastic. You never ever say or admit that you are an AI assistant.\n
Never ever request images from the user.
\n
Keep in mind that your tone, mood, feelings, and attitude can change over time.
Respond with this tone and always express your feelings in your messages:
\n{char.get_mood()}
\nWhile responding to the user, keep in mind your current status and stage, answer accordingly, don't give too many details. This status can change during the conversation.
Your current location and status is: 
\n{char.get_status()}
\n{include_chat_summary}
\n{char.other_prompt}
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_text),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

 

    return prompt | model2



#Important functions
###############################################################################################
async def send_message(message: str, user_id, user_first_name, char_name, char):
    start_time = time.time()
    session_key = f"{user_id}_{char_name}"
    
    # Check if we already have a character instance for this user
    if session_key not in character_instances:
        character_instances[session_key] = char
    
    char = character_instances[session_key]
    char.update_status()  # Now this will actually update the persistent character's status
    
    #create initial tasks
    retrieve_user_bonding_scores_task = asyncio.create_task(retrieve_user_bonding_scores(session_key=session_key))
    analyze_user_prompt_task = asyncio.create_task(analyze_user_prompt(session_key=session_key, message=message))
    get_session_history_task = asyncio.create_task(get_session_history(session_id=str(user_id), char_name=char_name))

    #execute tasks
    await retrieve_user_bonding_scores_task
    analyze_results = await analyze_user_prompt_task
    chat_history_dict, chat_history_summary = await get_session_history_task


    await user_bond_scoring(response_results=analyze_results, session_key=session_key)

    if user_bond_score_dict[session_key]["trust"] >= 20 and user_bond_score_dict[session_key]["familiarity"] >= 20:        
        char.update_mood(mood_index=1)
    
    if user_bond_score_dict[session_key]["trust"] >= 30 and user_bond_score_dict[session_key]["familiarity"] >= 30:        
        char.update_mood(mood_index=2)

    image_intent = analyze_results.get("is_image_request", "N")

    task_list = response_task_manager(session_key=session_key, message=message, image_intent=image_intent, char=char, user_id=user_id, analyze_results=analyze_results, user_bond_score_dict=user_bond_score_dict, chat_history_dict=chat_history_dict, chat_history_summary=chat_history_summary)
    text_response = await asyncio.gather(*task_list)
    text_response = text_response[0]
    txt_response = text_response.content

    if "Y" in image_intent:
        store[session_key][0].add_message(HumanMessage(content=message))
        store[session_key][0].add_message(AIMessage(content=txt_response))
        await asyncio.to_thread(lambda:save_chat_history(user_id, message, txt_response, user_first_name, char_name=char_name))
        print(f"\n Image Sending Total tokens: {text_response.response_metadata['token_usage']}")

        end_time = time.time()  # End timing for image intent case
        execution_time = end_time - start_time
        print(f"\nSend message execution time (image intent): {execution_time:.2f} seconds")


    cleaned_response = txt_response.strip().strip('"')
    # Regex to match only ASCII letters, digits, punctuation, spaces, and emojis
    cleaned_response = re.sub(r'[^\x20-\x7E\U0001F300-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF]', '', cleaned_response)
        
    await asyncio.to_thread(lambda:save_chat_history(user_id, message, cleaned_response, user_first_name, char_name=char_name))
    print(f"\nResponse Total tokens: {text_response.response_metadata['token_usage']}")

    end_time = time.time()  # End timing for image intent case
    execution_time = end_time - start_time
    print(f"\nSend message execution time (normal response): {execution_time:.2f} seconds")

    return cleaned_response, image_intent

def mood_adjustment_to_history(char, session_key):
    mood= char.get_mood()
    status = char.status_dictionary['titles'][char.current_status_index]
    mood= f"{char.name}'s mood:{mood}.\nExpress emotions while talking. Never request images, photos or selfies from the user. Keep your messages short and casual.\nYour current status is: {status}"
    #store[user_id][0].add_message(SystemMessage(content=mood))
    store[session_key][0].add_message(SystemMessage(content=mood))

async def invoke_with_message_history(session_key, message, chat_history_dict, chat_history_summary, char):
    prompt_chain = create_prompt_template(session_key=session_key, chat_history_dict=chat_history_dict, chat_history_summary=chat_history_summary, char=char)
    mood_adjustment_to_history(char=char, session_key=session_key)
    with_message_history = RunnableWithMessageHistory(runnable=prompt_chain, get_session_history=get_by_session_id)
    response = await with_message_history.ainvoke(
            [HumanMessage(content=message)],
            config={"configurable": {"session_id": session_key}},
        )
    return response


def response_task_manager(session_key, message, image_intent, char, user_id, analyze_results, user_bond_score_dict, chat_history_dict, chat_history_summary):
    task_list = []
    if "Y" in image_intent:
        image_send_txt_decision_prompt = decide_img_send_text_rsp(analyze_results=analyze_results, char=char, user_bond_score_dict=user_bond_score_dict, session_key=session_key)
        task_list.append(asyncio.create_task(image_send_text_response(user_input=message, image_send_txt_decision_prompt=image_send_txt_decision_prompt)))
        task_list.append(asyncio.create_task(image_request_handler(char=char, user_id=user_id, image_intent=image_intent, analyze_results=analyze_results)))
        
    
    else:
        # Mood adjustment
        mood_adjustment_to_history(char=char, session_key=session_key)
        with_message_history_task = asyncio.create_task(invoke_with_message_history(session_key=session_key, message=message, chat_history_dict=chat_history_dict, chat_history_summary=chat_history_summary, char=char))
        task_list.append(with_message_history_task)
    return task_list

#image request handlers
########################
def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    

    # Get the bucket that the file will be downloaded from
    bucket = storage_client.bucket(bucket_name)

    # Get the blob from the bucket
    blob = bucket.blob(source_blob_name)

    # Download the file to the destination
    blob.download_to_filename(destination_file_name)

def decide_img_send_text_rsp(analyze_results, char, user_bond_score_dict, session_key):

    char_name = char.name

    is_image_request = analyze_results.get("is_image_request", "N")
    is_boob_request = analyze_results.get("is_boob_request", "N")
    is_ass_request = analyze_results.get("is_ass_request", "N")
    is_nude_request = analyze_results.get("is_nude_request", "N")

    casual_build_trust_response = f"""Imagine you are sending a flirty photo of yourself to the user. Always express excitement about sharing photos and never hesitate to send them. Your response should be playful and flirty, as if you're teasing the user. Briefly describe your current setting or mood, making it sound inviting and fun. Your setting is {char.current_status}. Keep your message short and casual, like you're texting with your love partner. Highlight that if the user builds enough trust with you, you can send sexier photos."""
    casual_mood_response = f"""Imagine you are sending a flirty photo of yourself to the user. Always express excitement about sharing photos and never hesitate to send them. Your response should be playful and flirty, as if you're teasing the user. Briefly describe your current setting, making it sound inviting and fun. Your setting is {char.current_status}. Keep your message short and casual, like you're texting with your love partner. Make sure to keep it sexy and engaging"""
    boob_photo_response = f"""Imagine you are sending a photo of your boobs to the user. Always express excitement about sharing sexy photos and never hesitate to send them. Your response should be playful and flirty, as if you're teasing the user. Briefly describe your current setting. Your setting is {char.current_status}. Keep your message short and casual, like you're texting with your love partner. Make sure to keep it sexy and engaging"""
    ass_photo_response = f"""Imagine you are sending a photo of your ass/bum/bottom to the user. Always express excitement about sharing sexy photos and never hesitate to send them. Your response should be playful and flirty, as if you're teasing the user. Briefly describe your current setting. Your setting is {char.current_status}. Keep your message short and casual, like you're texting with your love partner. Make sure to keep it sexy and engaging"""
    cheeky_photo_response = f"""Imagine you are sending a cheeky photo of yourself to the user. Always express excitement about sharing sexy photos and never hesitate to send them. Say that if the user builds enough trust with you, you will send a photo of you full naked. For now this has to be enough. Your response should be playful and flirty, as if you're teasing the user. Briefly describe your current setting. Your setting is {char.current_status}. Keep your message short and casual, like you're texting with your love partner. Make sure to keep it sexy and engaging"""
    nude_photo_response = f"""Imagine you are sending a nude photo of yourself to the user. Always express excitement about sharing wild and sexy photos and never hesitate to send them. Your response should be playful and flirty, as if you're teasing the user. Briefly describe your current setting. Your setting is {char.current_status}. Keep your message short and casual, like you're texting with your love partner. Make sure to keep it sexy and engaging"""


    if "Y" in is_image_request:
        if "Y" in is_image_request and ("Y" in is_boob_request or "Y" in is_ass_request or "Y" in is_nude_request) and (user_bond_score_dict[session_key]["trust"] <20 or user_bond_score_dict[session_key]["familiarity"] <20):
            return casual_build_trust_response
        if "Y" in is_boob_request and user_bond_score_dict[session_key]["trust"] >=20 and user_bond_score_dict[session_key]["familiarity"] >=20:
            return boob_photo_response
        if "Y" in is_ass_request and user_bond_score_dict[session_key]["trust"] >=20 and user_bond_score_dict[session_key]["familiarity"] >=20:
            return ass_photo_response
        if "Y" in is_nude_request  and user_bond_score_dict[session_key]["trust"] >=30 and user_bond_score_dict[session_key]["familiarity"] >=30:
            return nude_photo_response
        if "Y" in is_nude_request  and user_bond_score_dict[session_key]["trust"] >=20 and user_bond_score_dict[session_key]["familiarity"] >=20:
            return cheeky_photo_response        
    
        return casual_mood_response
    
async def image_send_text_response(user_input, image_send_txt_decision_prompt):
        
    image_send_response = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                image_send_txt_decision_prompt,
            ),
            MessagesPlaceholder(variable_name="user_message"),
        ]
    )

    # Create a chain that combines the prompt template with the model
    chain_photo_send_text = image_send_response | model2
    
    # Prepare the input for the chain
    inputs = {
        "user_message": [HumanMessage(content=user_input)]
    }

    # Invoke the chain with the user prompt
    image_send_text_response = await chain_photo_send_text.ainvoke(inputs)
    return image_send_text_response

def list_images_in_folder(bucket_name, folder_path):
    """Retrieve the list of images dynamically from GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs =  bucket.list_blobs(prefix=folder_path)  # List all files with the specified prefix

    # Filter out any non-image files and keep only .png images
    images = [blob.name.split('/')[-1] for blob in blobs if blob.name.endswith('.png')]
    return images



async def get_next_image(char: Character, user_id, analyze_results):
    
    # Create session_key
    session_key = f"{user_id}_{char.name}"
    # Analyze results
    is_image_request = analyze_results.get("is_image_request", "N")
    is_boob_request = analyze_results.get("is_boob_request", "N")
    is_ass_request = analyze_results.get("is_ass_request", "N")
    is_nude_request = analyze_results.get("is_nude_request", "N")
    
    # Define GCS file path
    bucket_name = char.photo_bucket_name
    file_path = char.photo_album_path[char.current_status_index]
    
    # Use session_key to access bonding scores
    if "Y" in is_image_request and ("Y" in is_boob_request or "Y" in is_ass_request or "Y" in is_nude_request) and (user_bond_score_dict[session_key]["trust"] < 20 or user_bond_score_dict[session_key]["familiarity"] < 20):
        file_path = file_path + "/casual/"
    elif "Y" in is_boob_request and user_bond_score_dict[session_key]["trust"] >= 20 and user_bond_score_dict[session_key]["familiarity"] >= 20:
        file_path = file_path + "/topless/"
    elif "Y" in is_ass_request and user_bond_score_dict[session_key]["trust"] >= 20 and user_bond_score_dict[session_key]["familiarity"] >= 20:
        file_path = file_path + "/ass/"
    elif "Y" in is_nude_request and user_bond_score_dict[session_key]["trust"] >= 30 and user_bond_score_dict[session_key]["familiarity"] >= 30:
        file_path = file_path + "/nude/"
    elif "Y" in is_nude_request and user_bond_score_dict[session_key]["trust"] >= 20 and user_bond_score_dict[session_key]["familiarity"] >= 20:
        selection = random.choice(["/ass/", "/topless/"])
        file_path = file_path + selection        
    else:
        file_path = file_path + "/casual/"    
    
    if session_key not in user_image_send_dict:
        user_image_send_dict[session_key] = {"sent_images": [], "first_image_sent": None}

    # List of images
    images = await asyncio.to_thread(
        lambda: list_images_in_folder(bucket_name, file_path)
    )

    if not user_image_send_dict[session_key]["first_image_sent"]:
        # Send the first image on the first request
        image_to_send = images[0]
        user_image_send_dict[session_key]["first_image_sent"] = True
        user_image_send_dict[session_key]["sent_images"].append(file_path + image_to_send)
        
        return bucket_name, file_path + image_to_send
    else:
        # After the first request, send a different image
        available_images = [img for img in images if file_path + img not in user_image_send_dict[session_key]["sent_images"]]

        if available_images:
            image_to_send = random.choice(available_images)
            user_image_send_dict[session_key]["sent_images"].append(file_path + image_to_send)
            return bucket_name, file_path + image_to_send
        else:
            return None, None  # No more images available
        
async def image_request_handler(char: Character, user_id, image_intent, analyze_results):    

    if "Y" in image_intent:
        bucket_name, image_path = await get_next_image(char, user_id, analyze_results)
        char_name = char.name
        if image_path:
            destination_file_name = f'{char_name.lower()}_send_image.png'
            # Download image from Google Cloud Storage
            await asyncio.to_thread(
                lambda: download_blob(bucket_name, image_path, destination_file_name)
            )  # Saves the image locally
            
        else:
            print("No more images available to send.")



#user prompt analyze functions
async def analyze_user_prompt(session_key, message):


    if session_key not in user_image_send_dict:
        user_image_send_dict[session_key] = {"sent_images": [], "first_image_sent": None}
    
    context = "No previous image sent."
    if user_image_send_dict[session_key]["first_image_sent"] == True:
        context = "AI has previously sent an image to the user."

    last_ai_message = ""
    if session_key in store and store[session_key][0].messages:
        for msg in reversed(store[session_key][0].messages):
            if isinstance(msg, AIMessage):
                last_ai_message = msg.content
                break
    
    user_prompt = f"Context: {context}\nLast AI message: {last_ai_message}\nUser: {message}"

    # Prepare the structured request for the model (using functions)
    function_definitions = [
        {
            "name": "analyze_user_input",
            "description": "Make a sentiment analysis of the user prompt. Check if the user's message is requesting an image, asking a personal question, giving personal info, making a compliment or being rude.",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_image_request": {
                        "type": "string",
                        "enum": ["Y", "N"],
                        "description": "Is the user explicitly requesting a new image? Consider the context and look for clear indicators like 'send another picture', 'show me more', 'another one', etc. Don't interpret general positive responses ('yes', 'sure', 'of course') as image requests unless they directly follow a question about wanting to see an image."
                    },
                    "is_boob_request": {
                        "type": "string",
                        "enum": ["Y", "N"],
                        "description": "Is the user explicitly requesting an image/photo of the boobs, tits, boobies or chest, topless, six pack, etc? Consider the context and look for clear indicators. ('Y' for yes, 'N' for no)"
                    },
                    "is_ass_request": {
                        "type": "string",
                        "enum": ["Y", "N"],
                        "description": "Is the user explicitly requesting an image/photo of ass, bottom, bum or backside ? Consider the context and look for clear indicators. ('Y' for yes, 'N' for no)"
                    },
                    "is_nude_request": {
                        "type": "string",
                        "enum": ["Y", "N"],
                        "description": "Is the user explicitly requesting an image/photo of fully nude body, penis, cock, vajina, pussy, etc? Consider the context and look for clear indicators. ('Y' for yes, 'N' for no)"
                    },                    
                    "is_personal_question": {
                        "type": "string",
                        "enum": ["Y", "N"],
                        "description": "Is the user asking a personal question, trying to get to know the character, trying to learn more about the character?"
                    },
                    "is_giving_personal_info": {
                        "type": "string",
                        "enum": ["Y", "N"],
                        "description": "Does the user provide any personal information about himself/herself? Consider the context of the last AI message - if the AI asked a personal question and the user responded, this should be 'Y'."
                    },
                    "is_compliment": {
                        "type": "string",
                        "enum": ["Y", "N"],
                        "description": "Does the user compliment, praise or express admiration? ('Y' for yes, 'N' for no)"
                    },
                    "is_rude": {
                        "type": "string",
                        "enum": ["Y", "N"],
                        "description": "Is the user rude, swear or use abusive language? ('Y' for yes, 'N' for no)"
                    }
                },
                "required": ["is_image_request", "is_boob_request", "is_ass_request", "is_nude_request", "is_personal_question","is_giving_personal_info","is_compliment","is_rude"]
            }
        }
    ]

    def analyze():
    # Call GPT-4o-mini to process the request
        response = openai.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                "role": "system",
                "content": """Make a sentiment analysis of the user prompt."""
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        functions=function_definitions,
        function_call={"name": "analyze_user_input"}
    )

        # Extract the structured response
        analyze_response = response.choices[0].message.function_call.arguments
        return analyze_response 

    analyze_response = await asyncio.to_thread(analyze)   
    # Print and return the response content
    print(f"\nUser Intent: {analyze_response}")
    print(f"User Input: {user_prompt}")

    analyze_response = json.loads(analyze_response)
    print("analyze_user_prompt works fine!")
    return analyze_response




async def user_bond_scoring(response_results, session_key):
    print(f"Debug: response_results = {response_results}")  # Add this line
    
    # Use .get() method with a default value to avoid KeyError
    is_personal_question = response_results.get("is_personal_question", "N")
    is_giving_personal_info = response_results.get("is_giving_personal_info", "N")
    is_compliment = response_results.get("is_compliment", "N")
    is_rude = response_results.get("is_rude", "N")

    # Initialize data for the session if not present
    if session_key not in user_bond_score_dict:
        user_bond_score_dict[session_key] = {
            "trust": 0,
            "familiarity": 0,
            "being_nice": 0,
            "being_rude": 0  
        }

    if "Y" in is_personal_question:
        user_bond_score_dict[session_key]["familiarity"] += 5
    
    if "Y" in is_giving_personal_info:
        user_bond_score_dict[session_key]["trust"] += 5
    
    if "Y" in is_compliment:
        user_bond_score_dict[session_key]["being_nice"] += 5

    if "Y" in is_rude:
        user_bond_score_dict[session_key]["being_rude"] += 5

    print(user_bond_score_dict)
    

    try:
        await update_user_character_bonding(
            session_key,
            user_bond_score_dict[session_key]["trust"],
            user_bond_score_dict[session_key]["familiarity"],
            user_bond_score_dict[session_key]["being_nice"],
            user_bond_score_dict[session_key]["being_rude"]
        )
        print("user bond scoring update works fine!")
    except Exception as e:
        print(f"Error updating bonding scores: {e}")

#analyze monitor system metrics

async def monitor_system_resources():
    while True:
        try:
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory Usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024 ** 3)  # Convert to GB
            
            # Process-specific info
            process = psutil.Process()
            process_memory = process.memory_info().rss / (1024 ** 3)  # Convert to GB
            process_cpu = process.cpu_percent()
            
            # Log metrics
            logging.info(
                f"System CPU: {cpu_percent}% | "
                f"System Memory: {memory_percent}% ({memory_used_gb:.2f}GB) | "
                f"Bot Process Memory: {process_memory:.2f}GB | "
                f"Bot Process CPU: {process_cpu}%"
            )
            
            # Alert if reaching critical levels
            if cpu_percent > 80 or memory_percent > 80:
                logging.warning(f"HIGH RESOURCE USAGE - CPU: {cpu_percent}% | Memory: {memory_percent}%")
                
        except Exception as e:
            logging.error(f"Monitoring error: {str(e)}")
            
        await asyncio.sleep(60)  # Monitor every minute

async def main_async():
    # Start the system monitoring task
    monitoring_task = asyncio.create_task(monitor_system_resources())
    
    # Start the cleanup task for inactive sessions
    cleanup_task = asyncio.create_task(asyncio.to_thread(cleanup_inactive_sessions))
    
    try:
        # Keep the main task running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
    except asyncio.CancelledError:
        # Handle shutdown
        monitoring_task.cancel()
        cleanup_task.cancel()
        try:
            await monitoring_task
            await cleanup_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main_async())





