import os

from dotenv import load_dotenv
import pandas as pd
import openai

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

# 2. Load CSV
df = pd.read_csv("VST_Plugins_List.csv")

# 3. Add new columns with placeholders
df["Plugin Type"] = "Placeholder"
df["Developer/Producer"] = "Placeholder"
df["Notes"] = "Placeholder"

# 4. Function that queries ChatGPT for plugin details
def get_plugin_details_from_chatgpt(plugin_name):
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
    response = openai.ChatCompletion.create(
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

# 5. Parse out fields from the ChatGPT response
def parse_chatgpt_response(response_text):
    # Expect lines in the format:
    # Type: ...
    # Developer: ...
    # Notes: ...
    # Basic, naive parser:
    details = {
        "Plugin Type": "Unknown",
        "Developer/Producer": "Unknown",
        "Notes": "Unknown"
    }
    for line in response_text.splitlines():
        if line.lower().startswith("type:"):
            details["Plugin Type"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("developer:"):
            details["Developer/Producer"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("notes:"):
            details["Notes"] = line.split(":", 1)[1].strip()
    return details

# 6. Iterate over each plugin, query ChatGPT, parse the response, and update DataFrame
for idx, row in df.iterrows():
    plugin_name = row["Name"]
    chatgpt_reply = get_plugin_details_from_chatgpt(plugin_name)
    parsed = parse_chatgpt_response(chatgpt_reply)
    df.at[idx, "Plugin Type"] = parsed["Plugin Type"]
    df.at[idx, "Developer/Producer"] = parsed["Developer/Producer"]
    df.at[idx, "Notes"] = parsed["Notes"]

# 7. Now 'df' has the updated columns
# You can save or display it
print(df.head(50))  # Shows the first 50 rows
df.to_csv("/mnt/data/VST_Plugins_List_Enriched.csv", index=False)
