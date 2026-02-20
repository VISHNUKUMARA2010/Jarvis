from googlesearch import search 
from groq import Groq  # Importing the Groq library to use its API.
from json import load, dump  # Importing function to read and write JSON files.
import datetime  # Importing the datetime module for real-time date and time information.
from Backend.LearningSystem import learn_from_conversation, get_relevant_learnings  # Import learning system
import config  # Import centralized configuration
import app_paths  # Import for correct file paths

# Load configuration from config.py
Username = config.USERNAME
Assistantname = config.ASSISTANT_NAME
GroqAPIKey = config.GROQ_API_KEY

# Initialize the Groq client with the provided API key.
client = Groq(api_key=GroqAPIKey)

# Define the system instructions for the chatbot.
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

# Try to load the chat log from a JSON file, or create an empty one if it doesn't exist.
try:
    with open(app_paths.get_data_path("ChatLog.json"), "r") as f:
        messages = load(f)  
except:
    with open(app_paths.get_data_path("ChatLog.json"), "w") as f:
        dump([], f)

# Function to perform a Google search and format the results.
def GoogleSearch(query):
    search_results = search(query)
    results = []
    for i, result in enumerate(search_results):
        if i >= 5:
            break
        results.append(result)
    
    Answer = f"The search results for '{query}' are:\n[start]\n"
    for i in results:
        Answer += f"{i}\n\n"

    Answer += "[end]"
    return Answer

# Function to clean up the answer by removing empty lines.
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

# Predefined chatbot conversation system message and an initial user message.
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

# Function to get real-time information like the current date and time.
def Information():
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data += f"Use This Real-time Information if needed:\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hour, {minute} minutes, {second} second.\n"
    return data

# Function to handle real-time search and response generation.
# Import the SetAssistantStatus function path.
import os

def SetAssistantStatus(Status):
    with open(os.path.join(app_paths.FRONTEND_FILES_DIR, 'Status.data'), "w", encoding='utf-8') as file:
        file.write(Status)

def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages

    SetAssistantStatus("Searching...")

    # Load the chat log from the JSON file.
    with open(app_paths.get_data_path("ChatLog.json"), "r") as f:
        messages = load(f)
    messages.append({
        "role": "user",
        "content": f"{prompt}",
        "timestamp": datetime.datetime.now().isoformat()
    })    

    # Add Google search result to the system chatbot messages.
    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    # Get learned facts for context
    learned_ctx = get_relevant_learnings()
    context_messages = [{"role": "system", "content": Information() + learned_ctx}] if learned_ctx else [{"role": "system", "content": Information()}]

    # Strip timestamps from messages before sending to API (API doesn't support timestamp field)
    api_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    # Generate a response using Groq client.
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=SystemChatBot + context_messages + api_messages,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer =""

    # Concatenate response chunks from the streaming output.
    for chunks in completion:
        if chunks.choices[0].delta.content:
            Answer += chunks.choices[0].delta.content

    # Clean up the response.
    Answer = Answer.strip().replace("</s>", "")
    messages.append({
        "role": "assistant",
        "content": Answer,
        "timestamp": datetime.datetime.now().isoformat()
    })

    # Save the updated chat log back to the JSON file.
    with open(app_paths.get_data_path("ChatLog.json"), "w") as f:
        dump(messages, f, indent=4)

    # Automatically learn from this conversation
    try:
        learn_from_conversation(prompt, Answer)
    except Exception as learning_error:
        print(f"Learning error: {learning_error}")  # Don't fail if learning fails

    # Remove the most recent syste message from the chatbot conversation.
    SystemChatBot.pop()
    SetAssistantStatus("")
    return AnswerModifier(Answer=Answer)

# Main entry point of the program for interactive querying.
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))
