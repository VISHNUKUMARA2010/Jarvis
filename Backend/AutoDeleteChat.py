"""
Automatic Chat History Deletion System
Deletes chat messages older than 7 days when enabled in preferences.
"""

import json
import os
from datetime import datetime, timedelta
import app_paths  # Import for correct file paths

CHATLOG_PATH = app_paths.get_data_path("ChatLog.json")
PREFERENCES_PATH = app_paths.get_data_path("Preferences.json")
LAST_CLEANUP_PATH = app_paths.get_data_path("LastCleanup.json")

def load_preferences():
    """Load user preferences."""
    try:
        with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"auto_delete_chat": False}

def should_run_cleanup():
    """Check if we should run cleanup (once per day)."""
    try:
        with open(LAST_CLEANUP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            last_cleanup = datetime.fromisoformat(data["last_cleanup"])
            # Run cleanup once per day
            if datetime.now() - last_cleanup < timedelta(days=1):
                return False
    except Exception:
        pass  # File doesn't exist or is invalid, run cleanup
    
    return True

def save_cleanup_timestamp():
    """Save the timestamp of the last cleanup."""
    try:
        with open(LAST_CLEANUP_PATH, "w", encoding="utf-8") as f:
            json.dump({"last_cleanup": datetime.now().isoformat()}, f)
    except Exception as e:
        print(f"Error saving cleanup timestamp: {e}")

def delete_old_messages():
    """Delete chat messages older than 7 days from ChatLog.json"""
    try:
        # Load preferences
        prefs = load_preferences()
        
        # Check if auto-delete is enabled
        if not prefs.get("auto_delete_chat", False):
            return
        
        # Check if we should run cleanup today
        if not should_run_cleanup():
            return
        
        # Load chat log
        if not os.path.exists(CHATLOG_PATH):
            return
        
        with open(CHATLOG_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                save_cleanup_timestamp()
                return
            messages = json.loads(content)
        
        if not messages:
            save_cleanup_timestamp()
            return
        
        # Calculate cutoff date (7 days ago)
        cutoff_date = datetime.now() - timedelta(days=7)
        
        # Try to find messages with timestamps
        # If messages don't have timestamps, we'll keep recent ones based on position
        cleaned_messages = []
        has_timestamps = False
        
        for message in messages:
            # Check if message has a timestamp field
            if "timestamp" in message:
                has_timestamps = True
                try:
                    msg_time = datetime.fromisoformat(message["timestamp"])
                    if msg_time >= cutoff_date:
                        cleaned_messages.append(message)
                except Exception:
                    # Invalid timestamp, keep the message
                    cleaned_messages.append(message)
            else:
                # No timestamp, we'll handle this after the loop
                cleaned_messages.append(message)
        
        # If no messages had timestamps, keep only the last 50 messages (recent conversation)
        if not has_timestamps and len(messages) > 50:
            cleaned_messages = messages[-50:]
        elif not has_timestamps:
            cleaned_messages = messages
        
        # Save cleaned messages
        with open(CHATLOG_PATH, "w", encoding="utf-8") as f:
            json.dump(cleaned_messages, f, indent=4)
        
        # Save cleanup timestamp
        save_cleanup_timestamp()
        
        deleted_count = len(messages) - len(cleaned_messages)
        if deleted_count > 0:
            print(f"[Auto-Delete] Removed {deleted_count} old messages from chat history")
        
    except Exception as e:
        print(f"[Auto-Delete] Error: {e}")

def add_timestamps_to_messages():
    """
    Add timestamps to existing messages if they don't have them.
    Called when saving new messages to ensure future messages have timestamps.
    """
    try:
        if not os.path.exists(CHATLOG_PATH):
            return
        
        with open(CHATLOG_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return
            messages = json.loads(content)
        
        if not messages:
            return
        
        # Add timestamp to messages that don't have one
        modified = False
        for message in messages:
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()
                modified = True
        
        if modified:
            with open(CHATLOG_PATH, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=4)
    
    except Exception as e:
        print(f"[Auto-Delete] Timestamp addition error: {e}")

# Run on import if needed
if __name__ == "__main__":
    print("Running auto-delete check...")
    delete_old_messages()
    print("Done!")
