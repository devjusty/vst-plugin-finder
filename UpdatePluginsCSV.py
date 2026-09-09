import pandas as pd
import time
import random
import os
import argparse
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI
from openai import RateLimitError

def main():
    parser = argparse.ArgumentParser(description="Enrich VST plugin CSV data using OpenAI.")
    parser.add_argument("--input", default="VST_Plugins_List.csv", help="Input CSV file to read (default: VST_Plugins_List.csv)")
    parser.add_argument("--output", default="VST_Plugins_List_Enriched.csv", help="Final CSV file to write (default: VST_Plugins_List_Enriched.csv)")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of plugins to process in this run")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of plugins to process before pausing (default: 5)")
    parser.add_argument("--delay", type=float, default=20.0, help="Seconds to wait between individual requests (default: 20)")
    parser.add_argument("--retries", type=int, default=5, help="Max retry attempts for API rate limits (default: 5)")
    parser.add_argument("--cache", default="plugin_cache.json", help="Path to the JSON cache file (default: plugin_cache.json)")
    args = parser.parse_args()

    load_dotenv()
    
    # Graceful check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: No OpenAI API key found in the environment.", file=sys.stderr)
        print("Please copy '.env.example' to '.env' and add your OPENAI_API_KEY.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI()

    # Determine progress file name based on input
    input_base = os.path.splitext(args.input)[0]
    progress_file = f"{input_base}_Progress.csv"

    # Load cache
    cache = {}
    if os.path.exists(args.cache):
        try:
            with open(args.cache, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded cache with {len(cache)} entries.")
        except json.JSONDecodeError:
            print(f"Warning: Cache file '{args.cache}' is invalid JSON. Starting fresh cache.")

    def save_cache():
        with open(args.cache, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)

    # Load CSV
    try:
        df = pd.read_csv(args.input)
        print(f"Loaded CSV with {len(df)} rows")
    except FileNotFoundError:
        print(f"Error: '{args.input}' file not found", file=sys.stderr)
        sys.exit(1)

    # Add new columns with placeholders if they don't exist
    if "Plugin Type" not in df.columns:
        df["Plugin Type"] = "Placeholder"
    if "Developer/Producer" not in df.columns:
        df["Developer/Producer"] = "Placeholder"
    if "Notes" not in df.columns:
        df["Notes"] = "Placeholder"

    # Try to load existing progress if any
    try:
        progress_df = pd.read_csv(progress_file)
        # Update only the columns we care about
        for idx, row in progress_df.iterrows():
            if idx < len(df) and idx < len(progress_df):
                df.at[idx, "Plugin Type"] = row["Plugin Type"]
                df.at[idx, "Developer/Producer"] = row["Developer/Producer"] 
                df.at[idx, "Notes"] = row["Notes"]
        print("Loaded existing progress file. Will resume from where we left off.")
    except FileNotFoundError:
        print("No existing progress file found. Starting from scratch.")

    def get_plugin_details_from_chatgpt(plugin_name):
        retries = 0
        base_wait_time = 2  # Start with 2 seconds
        
        while retries <= args.retries:
            try:
                prompt = f"""
                The following is the name of a VST plugin: '{plugin_name}'.
                Provide concise details about its:
                - Plugin Type (e.g., EQ, Compressor, Synth, etc.)
                - Developer or Producer
                - Additional notes (brief)
                If uncertain, respond with "Unknown" for that field.
                
                You must return your answer as a JSON object with exactly these three keys:
                "Plugin Type", "Developer/Producer", and "Notes".
                """
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", 
                         "content": "You are a helpful assistant specialized in VST plugin details. Output valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=150,
                    temperature=0.2
                )
                
                return response.choices[0].message.content.strip()
                
            except RateLimitError:
                if retries >= args.retries:
                    print(f"Max retries reached for '{plugin_name}'. Giving up after {retries} attempts.")
                    return json.dumps({"Plugin Type": "Unknown", "Developer/Producer": "Unknown", "Notes": "Rate Limit Error"})
                
                wait_time = base_wait_time * (2 ** retries) + random.uniform(0, 1)
                print(f"Rate limit hit for '{plugin_name}'. Retry {retries+1}/{args.retries} after {wait_time:.2f} seconds")
                time.sleep(wait_time)
                retries += 1
                
            except Exception as e:
                print(f"Error querying API for '{plugin_name}': {e}")
                return json.dumps({"Plugin Type": "Unknown", "Developer/Producer": "Unknown", "Notes": f"API Error: {str(e)[:100]}"})

    def parse_chatgpt_response(response_text):
        details = {
            "Plugin Type": "Unknown",
            "Developer/Producer": "Unknown",
            "Notes": "Unknown"
        }
        
        try:
            parsed = json.loads(response_text)
            details["Plugin Type"] = parsed.get("Plugin Type", "Unknown")
            details["Developer/Producer"] = parsed.get("Developer/Producer", "Unknown")
            details["Notes"] = parsed.get("Notes", "Unknown")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {response_text}")
        
        return details

    def process_batch(start_idx, current_batch_size):
        end_idx = min(start_idx + current_batch_size, len(df))
        if args.limit and end_idx > args.limit:
            end_idx = args.limit
            
        for idx in range(start_idx, end_idx):
            row = df.iloc[idx]
            plugin_name = row.get("Name", "Unknown")
            size_bytes = row.get("SizeBytes", "0")
            last_write = row.get("LastWriteTime", "Unknown")
            
            cache_key = f"{plugin_name}_{size_bytes}_{last_write}"
            
            print(f"Processing {idx+1}/{len(df)}: {plugin_name}")
            
            # Skip if already processed in CSV (for resuming without cache)
            if df.at[idx, "Plugin Type"] != "Placeholder" and df.at[idx, "Developer/Producer"] != "Placeholder":
                print(f"Skipping already processed plugin in CSV: {plugin_name}")
                continue
                
            # Check cache
            if cache_key in cache:
                print(f"Using cached data for: {plugin_name}")
                parsed = cache[cache_key]
                time_to_wait = 0
            else:
                chatgpt_reply = get_plugin_details_from_chatgpt(plugin_name)
                parsed = parse_chatgpt_response(chatgpt_reply)
                
                # Update cache
                cache[cache_key] = parsed
                save_cache()
                
                # Wait between requests to avoid hitting rate limits
                time_to_wait = args.delay
            
            df.at[idx, "Plugin Type"] = parsed.get("Plugin Type", "Unknown")
            df.at[idx, "Developer/Producer"] = parsed.get("Developer/Producer", "Unknown")
            df.at[idx, "Notes"] = parsed.get("Notes", "Unknown")
            
            # Save progress for each item to avoid data loss
            df.to_csv(progress_file, index=False)
            
            if time_to_wait > 0 and (idx < end_idx - 1 or (end_idx < len(df) and (not args.limit or end_idx < args.limit))):
                time.sleep(time_to_wait)

    total_to_process = len(df)
    if args.limit and args.limit < total_to_process:
        total_to_process = args.limit
        print(f"Limiting execution to {args.limit} plugins.")

    for batch_start in range(0, total_to_process, args.batch_size):
        print(f"\nProcessing batch starting at index {batch_start}")
        process_batch(batch_start, args.batch_size)
        
        # Save after each batch
        df.to_csv(args.output, index=False)
        print(f"Completed batch. Progress saved.")
        
    print("\nAll processing complete!")
    print(f"Final results saved to {args.output}")
    
    # Display sample of results
    print("\nSample of processed data:")
    print(df.head(5))

if __name__ == "__main__":
    main()
