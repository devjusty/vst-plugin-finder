import pandas as pd
import time
import random
from dotenv import load_dotenv
from openai import OpenAI
from openai import RateLimitError

load_dotenv()
client = OpenAI()

# 2. Load CSV
try:
    df = pd.read_csv("VST_Plugins_List.csv")
    print(f"Loaded CSV with {len(df)} rows")
except FileNotFoundError:
    print("Error: VST_Plugins_List.csv file not found")
    exit(1)

# 3. Add new columns with placeholders if they don't exist
if "Plugin Type" not in df.columns:
    df["Plugin Type"] = "Placeholder"
if "Developer/Producer" not in df.columns:
    df["Developer/Producer"] = "Placeholder"
if "Notes" not in df.columns:
    df["Notes"] = "Placeholder"

# 4. Function that queries ChatGPT for plugin details with exponential backoff
def get_plugin_details_from_chatgpt(plugin_name, max_retries=5):
    retries = 0
    base_wait_time = 2  # Start with 2 seconds
    
    while retries <= max_retries:
        try:
            # You can customize the prompt as needed
            prompt = f"""
            The following is the name of a VST plugin: '{plugin_name}'.
            Provide concise details about its:
            - Plugin Type (e.g., EQ, Compressor, Synth, etc.)
            - Developer or Producer
            - Additional notes (brief)
            If uncertain, respond with "Unknown" for that field.
            Return your answer in the format:
            Type: <value>
            Developer: <value>
            Notes: <value>
            """
            
            # Use the ChatCompletion API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", 
                     "content": "You are a helpful assistant specialized in VST plugin details."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )
            
            # Extract the model's reply
            content = response.choices[0].message.content.strip()
            return content
            
        except RateLimitError as e:
            if retries >= max_retries:
                print(f"Max retries reached for '{plugin_name}'. Giving up after {retries} attempts.")
                return "Type: Unknown\nDeveloper: Unknown\nNotes: Rate Limit Error"
            
            # Exponential backoff with jitter
            wait_time = base_wait_time * (2 ** retries) + random.uniform(0, 1)
            print(f"Rate limit hit for '{plugin_name}'. Retry {retries+1}/{max_retries} after {wait_time:.2f} seconds")
            time.sleep(wait_time)
            retries += 1
            
        except Exception as e:
            print(f"Error querying API for '{plugin_name}': {e}")
            return f"Type: Unknown\nDeveloper: Unknown\nNotes: API Error: {str(e)[:100]}"

# 5. Parse out fields from the ChatGPT response
def parse_chatgpt_response(response_text):
    # Expect lines in the format:
    # Type: ...
    # Developer: ...
    # Notes: ...
    # Basic parser:
    details = {
        "Plugin Type": "Unknown",
        "Developer/Producer": "Unknown",
        "Notes": "Unknown"
    }
    
    try:
        for line in response_text.splitlines():
            if line.lower().startswith("type:"):
                details["Plugin Type"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("developer:"):
                details["Developer/Producer"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("notes:"):
                details["Notes"] = line.split(":", 1)[1].strip()
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response was: {response_text}")
    
    return details

# 6. Function to process a batch of plugins
def process_batch(start_idx, batch_size):
    end_idx = min(start_idx + batch_size, len(df))
    
    for idx in range(start_idx, end_idx):
        row = df.iloc[idx]
        plugin_name = row["Name"]
        print(f"Processing {idx+1}/{len(df)}: {plugin_name}")
        
        # Skip if already processed (for resuming)
        if df.at[idx, "Plugin Type"] != "Placeholder" and df.at[idx, "Developer/Producer"] != "Placeholder":
            print(f"Skipping already processed plugin: {plugin_name}")
            continue
        
        chatgpt_reply = get_plugin_details_from_chatgpt(plugin_name)
        parsed = parse_chatgpt_response(chatgpt_reply)
        
        df.at[idx, "Plugin Type"] = parsed["Plugin Type"]
        df.at[idx, "Developer/Producer"] = parsed["Developer/Producer"]
        df.at[idx, "Notes"] = parsed["Notes"]
        
        # Save progress for each item to avoid data loss
        df.to_csv("VST_Plugins_List_Progress.csv", index=False)
        
        # Wait between requests to avoid hitting rate limits
        # For OpenAI's free tier, reasonable limits are ~3 requests per minute
        time.sleep(20)  # 20 second delay between requests

# 7. Main execution with batch processing
def main():
    # Try to load existing progress if any
    try:
        progress_df = pd.read_csv("VST_Plugins_List_Progress.csv")
        # Update only the columns we care about
        for idx, row in progress_df.iterrows():
            if idx < len(df):
                df.at[idx, "Plugin Type"] = row["Plugin Type"]
                df.at[idx, "Developer/Producer"] = row["Developer/Producer"] 
                df.at[idx, "Notes"] = row["Notes"]
        print("Loaded existing progress file. Will resume from where we left off.")
    except FileNotFoundError:
        print("No existing progress file found. Starting from scratch.")
    
    batch_size = 5  # Process in small batches
    for batch_start in range(0, len(df), batch_size):
        print(f"\nProcessing batch starting at index {batch_start}")
        process_batch(batch_start, batch_size)
        
        # Save after each batch
        df.to_csv("VST_Plugins_List_Enriched.csv", index=False)
        print(f"Completed batch. Progress saved.")
        
        # Optional: pause between batches
        if batch_start + batch_size < len(df):
            pause_time = 30  # 30 seconds between batches
            print(f"Pausing for {pause_time} seconds before next batch...")
            time.sleep(pause_time)
    
    print("\nAll processing complete!")
    print("Final results saved to VST_Plugins_List_Enriched.csv")
    
    # Display sample of results
    print("\nSample of processed data:")
    print(df.head(5))

if __name__ == "__main__":
    main()
