import os
from google import genai
from google.genai.errors import APIError

# ⚠️ SECURITY NOTE: Replace 'YOUR_API_KEY_HERE' with your actual key.
# This method is less secure than using environment variables.
# It is best practice to never commit actual keys to version control (e.g., Git).
MY_API_KEY = ''

def list_available_models_with_key():
    """
    Lists all available models using an API key defined inside the script.
    """
    if MY_API_KEY == 'YOUR_API_KEY_HERE':
        print("🚨 Please replace 'YOUR_API_KEY_HERE' with your actual Gemini API key.")
        return

    print("🤖 Attempting to connect to the Gemini API...")

    # 1. Configuration (Pass the API Key directly)
    try:
        # Pass the key directly to the Client constructor
        client = genai.Client(api_key=MY_API_KEY)
    except Exception as e:
        print(f"Error initializing client: {e}")
        return

    print("✅ Connection successful.")
    print("\nAvailable Gemini Models:\n")

    # 2. Model Listing
    try:
        models = client.models.list()
        
        # 3. Displaying Results
        for model in models:
            # Filtering for core models relevant to content generation
            if model.name.startswith("models/gemini") or model.name.startswith("models/text"):
                print(f"  Name: **{model.name}**")
                print(f"  Description: {model.description[:100]}...")
                print(f"  Input Tokens: {model.input_token_limit}")
                print(f"  Output Tokens: {model.output_token_limit}")
                print("-" * 30)

    except APIError as e:
        print(f"\n[API ERROR] Could not retrieve models: {e}")
        print("The API key might be invalid or have incorrect permissions.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    list_available_models_with_key()