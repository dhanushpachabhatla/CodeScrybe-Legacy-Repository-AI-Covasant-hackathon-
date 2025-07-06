import os
import json
import time
import re
import tiktoken
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# INPUT_FILE = "parsed_output.json"
INPUT_FILE = "parsed_output_cobol_bank_system_repo.json"
OUTPUT_FILE = "new_updated_ner_DOOM.json"
CACHE_FILE = "newcache_of_updated_ner_DOOM.json"

TOK_LIMIT = 6000  # stay below Gemini 8192
encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")  # still fine for token counting

# Load parsed code chunks
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

# Load or initialize cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

results = []

def count_tokens(text):
    return len(encoder.encode(text))

def create_prompt(batch):
    formatted_chunks = "\n\n".join([
        f"---\nFile: {c['file']}\nChunk ID: {c['chunk_id']}\nLanguage: {c['language']}\n\n{c['code']}\n---"
        for c in batch
    ])
    return f"""
You are an expert software analyst. For each code segment, extract the following in structured JSON format:

[
  {{
    "file": "...",
    "chunk_id": 0,
    "language": "...",
    "feature": "...",
    "description": "...",
    "functions": [
        {{
            "name": "...",
            "signature": "...",
            "start_line": 0,
            "end_line": 0,
            "class": "Optional enclosing class name"
        }}
    ],
    "classes": [
        {{
            "name": "...",
            "parent_class": "...",
            "methods": ["...", "..."]
        }}
    ],
    "apis": ["API_1", "API_2"],
    "database_tables": ["table1", "table2"],
    "inputs": ["..."],
    "outputs": ["..."],
    "dependencies": ["..."],
    "side_effects": ["..."],
    "requirements": ["..."],
    "comments": [
        {{
            "content": "...",
            "type": "inline|block|docstring",
            "line_number": 0
        }}
    ],
    "annotations": {{
      "developer_notes": "..."
    }}
  }}
]

Code:
{formatted_chunks}
""".strip()

def clean_json_string(text):
    # Remove markdown-style JSON fencing
    if text.strip().startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text.strip())
    return text

# Token-aware batching
# Instead of one global chunk, build a mapping: file -> chunk 0
global_chunks = {c["file"]: c for c in chunks if c["chunk_id"] == 0}

# Token-aware batching
batches = []
current_batch = []
current_file = None

for chunk in chunks:
    if chunk["chunk_id"] == 0:
        continue  # skip global chunks from main list

    # Check if global chunk for this file exists
    file_global_chunk = global_chunks.get(chunk["file"])

    test_batch = current_batch + [chunk]
    code_blob = "\n\n".join([c['code'] for c in test_batch])

    # Include the file's global chunk (if not already included)
    if file_global_chunk and file_global_chunk not in test_batch:
        code_blob = file_global_chunk['code'] + "\n\n" + code_blob

    token_count = count_tokens(code_blob)
    if token_count > TOK_LIMIT:
        if current_batch:
            batches.append(current_batch)
        current_batch = [chunk]  # Start new batch
    else:
        current_batch.append(chunk)

if current_batch:
    batches.append(current_batch)

print(f"📦 Total batches prepared: {len(batches)}")


# Use gemini-1.5-pro via new SDK
# model = client.models.get(name = "models/gemini-2.0-flash")

for i, batch in enumerate(batches):
    batch_key = f"batch_{i}"

    if batch_key in cache:
        print(f"✅ Skipping cached {batch_key}")
        results.extend(cache[batch_key])
        continue

    print(f"🚀 Processing {batch_key}...")

    file_global_chunk = global_chunks.get(batch[0]["file"])
    if file_global_chunk and file_global_chunk not in batch:
        batch = [file_global_chunk] + batch

    prompt = create_prompt(batch)

    try:
        response = client.models.generate_content(
            model = "gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text
        print(raw)
        cleaned = clean_json_string(raw)
        output_json = json.loads(cleaned)

        results.extend(output_json)

        for item in output_json:
            file = item["file"]
            chunk_id = item["chunk_id"]
            match = next((c for c in batch if c["file"] == file and c["chunk_id"] == chunk_id), None)
            if match:
                item["code"] = match["code"]
        

        
        cache[batch_key] = output_json

        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)

        time.sleep(1.2)  # stay within 60 RPM
    except Exception as e:
        print(f"❌ Error in {batch_key}: {e}")
        continue

# Save final result
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Feature extraction complete. Results saved to {OUTPUT_FILE}")
