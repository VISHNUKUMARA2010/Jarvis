"""
Automatic Learning System for Jarvis AI
This module enables Jarvis to learn automatically from conversations and user interactions.

HOW IT WORKS:
1. After each conversation, the system analyzes the exchange using AI
2. It extracts meaningful facts, preferences, and information about the user
3. Learned facts are stored in LearningMemory.json with timestamps
4. The most relevant learned facts are included in future conversations
5. Jarvis uses this information to provide personalized responses

WHAT IT LEARNS:
- User preferences and likes/dislikes
- Personal information shared in conversations
- Goals, plans, and intentions
- Interests and hobbies
- Recurring topics and concerns
- Important context about the user's life

FEATURES:
- Automatic extraction: No manual input needed
- Duplicate prevention: Similar facts are merged
- Relevance tracking: Frequently mentioned facts are prioritized
- Memory limit: Keeps the 100 most relevant learnings
- Privacy: All data stored locally in LearningMemory.json

USAGE:
The system works automatically - just have conversations with Jarvis and it will learn!
You can clear learned memory anytime from Settings → Preferences → Clear Learned Memory
"""

from groq import Groq
from json import load, dump
from datetime import datetime
import os
import config  # Import centralized configuration
import app_paths  # Import for correct file paths

# Load configuration from config.py
Username = config.USERNAME
Assistantname = config.ASSISTANT_NAME
GroqAPIKey = config.GROQ_API_KEY

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# Path to learning memory file
LEARNING_MEMORY_PATH = app_paths.get_data_path("LearningMemory.json")

def load_learning_memory():
    """Load the learning memory from JSON file."""
    try:
        with open(LEARNING_MEMORY_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return load(open(LEARNING_MEMORY_PATH, "r", encoding="utf-8"))
            return []
    except FileNotFoundError:
        with open(LEARNING_MEMORY_PATH, "w", encoding="utf-8") as f:
            dump([], f)
        return []

def save_learning_memory(memory):
    """Save the learning memory to JSON file."""
    with open(LEARNING_MEMORY_PATH, "w", encoding="utf-8") as f:
        dump(memory, f, indent=4, ensure_ascii=False)

def extract_learnings(user_query, assistant_response):
    """
    Analyze the conversation and extract important learnings using AI.
    Returns a list of learned facts.
    """
    try:
        # Prompt for extracting learnings
        extraction_prompt = f"""Analyze this conversation between the user and assistant and extract any important facts, preferences, or information about the user that should be remembered for future conversations.

User: {user_query}
Assistant: {assistant_response}

Extract ONLY significant facts worth remembering, such as:
- User's preferences, likes/dislikes
- Personal information or experiences shared
- Goals, plans, or intentions mentioned
- Important context about their life, work, or interests
- Recurring topics or concerns

Format: Return each learning as a brief, clear statement. If there's nothing significant to learn, respond with "NONE".

Example output format:
- User prefers coffee over tea
- User is learning Python programming
- User has a meeting tomorrow at 3pm

Extracted learnings:"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a learning extraction system. Extract only meaningful, important facts from conversations that would be useful to remember in the future."},
                {"role": "user", "content": extraction_prompt}
            ],
            max_tokens=200,
            temperature=0.3,
        )

        result = response.choices[0].message.content.strip()
        
        # Parse the result
        if result.upper() == "NONE" or not result:
            return []
        
        # Extract learnings (each line starting with -)
        learnings = []
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                fact = line[1:].strip()
                if fact and len(fact) > 5:  # Only keep substantial facts
                    learnings.append(fact)
        
        return learnings
    
    except Exception as e:
        print(f"Learning extraction error: {e}")
        return []

def add_learning(fact):
    """Add a new learning to memory."""
    memory = load_learning_memory()
    
    # Create learning entry
    entry = {
        "fact": fact,
        "timestamp": datetime.now().isoformat(),
        "relevance_count": 1
    }
    
    # Check if similar fact already exists (basic duplicate prevention)
    fact_lower = fact.lower()
    for existing in memory:
        if existing["fact"].lower() == fact_lower:
            # Update existing fact
            existing["relevance_count"] += 1
            existing["timestamp"] = datetime.now().isoformat()
            save_learning_memory(memory)
            return
    
    # Add new fact
    memory.append(entry)
    
    # Keep only last 100 learnings (to prevent unlimited growth)
    if len(memory) > 100:
        memory = sorted(memory, key=lambda x: (x["relevance_count"], x["timestamp"]), reverse=True)[:100]
    
    save_learning_memory(memory)

def learn_from_conversation(user_query, assistant_response):
    """
    Automatically learn from a conversation exchange.
    This is called after each user-assistant interaction.
    """
    learnings = extract_learnings(user_query, assistant_response)
    
    for learning in learnings:
        add_learning(learning)
    
    return len(learnings)

def get_relevant_learnings(max_facts=10):
    """
    Get the most relevant learnings to include in conversation context.
    Returns a formatted string of learned facts.
    """
    memory = load_learning_memory()
    
    if not memory:
        return ""
    
    # Sort by relevance and recency
    sorted_memory = sorted(memory, key=lambda x: (x["relevance_count"], x["timestamp"]), reverse=True)
    
    # Get top facts
    top_facts = sorted_memory[:max_facts]
    
    if not top_facts:
        return ""
    
    # Format for system prompt
    facts_text = "\n*** What I've learned about you from our conversations: ***\n"
    for fact in top_facts:
        facts_text += f"- {fact['fact']}\n"
    
    return facts_text

def clear_learning_memory():
    """Clear all learned information."""
    save_learning_memory([])

# Test function
if __name__ == "__main__":
    print("Learning System Test")
    print("Current learnings:", get_relevant_learnings())
