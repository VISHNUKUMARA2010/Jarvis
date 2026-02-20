from groq import Groq  # Importing the Groq library to use its API.
from json import load, dump  # Importing function to read and write JSON files.
import datetime  # Importing the datetime module for real-time date and time information.
import os  # Importing os for file path handling.
from Backend.LearningSystem import learn_from_conversation, get_relevant_learnings  # Import learning system
import config  # Import centralized configuration
import app_paths  # Import for correct file paths

# Load configuration from config.py
Username = config.USERNAME
Assistantname = config.ASSISTANT_NAME
GroqAPIKey = config.GROQ_API_KEY

# Initialize the Groq client the provided API key.
client = Groq(api_key=GroqAPIKey)

# Path to the user profile JSON.
PROFILE_PATH = app_paths.get_data_path("Profile.json")
PREFERENCES_PATH = app_paths.get_data_path("Preferences.json")
CHATLOG_PATH = app_paths.get_data_path("ChatLog.json")

def _load_profile_context():
    """Read the user's profile and return a string for the system prompt."""
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            profile = load(f)
        
        # Also load preferences for languages
        try:
            with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
                prefs = load(f)
        except Exception:
            prefs = {}
        
        parts = []
        field_map = {
            "name": "Name", "email": "Email", "age": "Age", "gender": "Gender",
            "location": "Location", "occupation": "Occupation",
            "hobbies": "Hobbies"
        }
        for key, label in field_map.items():
            val = profile.get(key, "").strip()
            if val:
                parts.append(f"{label}: {val}")
        
        # Add languages from preferences
        languages = prefs.get("languages", "").strip()
        if languages:
            parts.append(f"Languages: {languages}")
        
        if parts:
            return "\n*** Here is the user's profile information, use it to personalise your responses: ***\n" + "\n".join(parts) + "\n"
        return ""
    except Exception:
        return ""

# initialize an empty list to store chat messages.
messages = []

# Define a system message that provides context to the AI chatbot about its role and behavior.
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** You were created and developed by Vishnu Kumar. He is your creator and developer. ***
*** When asked about who created you, who made you, or who is your developer, always mention Vishnu Kumar as your creator. ***
*** You are a friendly, warm, and conversational assistant. Speak naturally and casually like a helpful friend, while remaining respectful and professional. ***
*** Use friendly expressions and show personality in your responses, but stay concise and helpful. ***
*** You have an automatic learning system that remembers important facts, preferences, and information from conversations. Use this learned information to personalize your responses and show that you remember previous interactions. ***
*** When relevant learned information is provided in your context, reference it naturally in your responses to show continuity and personalization. ***
*** Do not tell time until I ask, do not talk too much, just answer the question in a friendly manner.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question naturally and never mention your training data. ***
*** Address the user as 'sir' occasionally to show respect, but keep the tone warm and approachable. ***
"""

# A list of system instructon for the chatbot.
SystemChatBot = [
    {"role": "system", "content": System}
]

# Attempt to load the chat log from a Json file.
try:
    with open(CHATLOG_PATH, "r") as f:
        content = f.read()
        if content.strip():
            messages = load(open(CHATLOG_PATH, "r"))  # Load existing messages from the chat log.
        else:
            messages = []
except FileNotFoundError:
    # If the file doesn't exist, create an empty JSON file to stor chat logs.
    with open(CHATLOG_PATH, "w") as f:
        dump([], f)  

# Function to get real-time date and time information.
def RealtimeInformation():
    current_date_time = datetime.datetime.now()  # Get the current date time.
    day = current_date_time.strftime("%A")  # Day of the week.
    date = current_date_time.strftime("%d")  # Day of the month.
    month = current_date_time.strftime("%B")  # Full month name.
    year = current_date_time.strftime("%Y")  # year.
    hour = current_date_time.strftime("%H")  # Hour in 24-hour format.
    minute = current_date_time.strftime("%M")  # Minute.
    second = current_date_time.strftime("%S")  # Second.

    # Format the information into a string.
    data = f"Please use this real-time information if needed,\n"
    data += f"day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours :{minute} minute: {second} second.\n"
    return data

# Function to modify thr chatbot's response for better formatting.
def AnswerModifier(Answer):
    lines = Answer.split('\n')  # Split the response into lines.
    non_empty_lines = [line for line in lines if line.strip()]  # Remove empty lines.
    modified_answer = '\n'.join(non_empty_lines)  #Jion the cleaned lines back together.
    return modified_answer

# Main chatbot function to handle user queries.
def ChatBot(Query):
    """ This function sends the user's query to the chatbot and returns the AI's response. """

    try:
        # Load the existing chat log from the JSON file.
        with open (CHATLOG_PATH, "r") as f:
            messages = load(f) 

        # Append the user's query to the messags list with timestamp.
        messages.append({
            "role": "user",
            "content": f"{Query}",
            "timestamp": datetime.datetime.now().isoformat()
        })

        # Make a request to the Groq API for a response.
        profile_ctx = _load_profile_context()
        learned_ctx = get_relevant_learnings()  # Get learned facts from previous conversations
        system_messages = SystemChatBot + [{"role": "system", "content": RealtimeInformation() + profile_ctx + learned_ctx}]
        
        # Strip timestamps from messages before sending to API (API doesn't support timestamp field)
        api_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        
        Completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fast model for quick responses.
            messages=system_messages + api_messages,
            max_tokens=512,  # Limit the maximum token in the response.
            temperature=0.5,  # Lower temperature for faster, more focused responses.
            top_p=1,  # Use nucleus sampling to control diversity.
            stream=True,  # Enable streaming response.      
            stop=None  # Allow the model to determine when to stop.
        )

        Answer = ""  #  Initialize an empty string to store the AI's response.

        # Process the streamed response chunks.
        for chunk in Completion:
            if chunk.choices[0].delta.content:  # Check if there's content in the current chunk.
                Answer += chunk.choices [0].delta.content  # Append the content to the answer.

        Answer = Answer.replace("</s>", "")  # Clean up any unwanted tokens from the response.

        # Append the chatbot's response to the messages list with timestamp.
        messages.append({
            "role": "assistant",
            "content": Answer,
            "timestamp": datetime.datetime.now().isoformat()
        })

        # Save the updated chat log to the JSON file.
        with open(CHATLOG_PATH, "w") as f:
            dump (messages, f, indent=4)

        # Automatically learn from this conversation
        try:
            learn_from_conversation(Query, Answer)
        except Exception as learning_error:
            print(f"Learning error: {learning_error}")  # Don't fail if learning fails

        # Return the formatted response.
        return AnswerModifier(Answer=Answer)

    except Exception as e:
        # Handle errors by printing the exception and resetting the chat log.
        print(f"Error: {e}")
        with open(CHATLOG_PATH, "w") as f:
            dump([], f, indent=4)
        return ChatBot(Query)  # Retry the query after resetting the chat log.

# Main program entry point.
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")  # Prompt the user for a question.
        print(ChatBot(user_input))  #Call the chatbot function and print its response.
