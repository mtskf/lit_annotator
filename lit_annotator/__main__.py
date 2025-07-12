import os
import re
import time
from pathlib import Path
from typing import List, Tuple
from textwrap import dedent
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
client = OpenAI()

# --- Configuration ---
CHUNK_SIZE = 500  # number of words per chunk

# --- Precompiled regex patterns ---
REF_PATTERN = re.compile(r"\[\^(\d+)\](?!:)")  # 注釈参照
DEF_PATTERN = re.compile(r"\[\^(\d+)\]:")      # 注釈定義

# --- Retry decorator ---
def retry(max_attempts=3, delay=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Error: {e} — retrying in {delay} seconds...")
                    time.sleep(delay)
            raise RuntimeError(f"Failed after {max_attempts} attempts")
        return wrapper
    return decorator

def detect_genre_intro(text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that classifies the genre of English book excerpts."
            },
            {
                "role": "user",
                "content": (
                    "Here is the beginning of a book. Based on the style, tone, and content, what is the most appropriate genre?\n\n"
                    + text[:1000] +
                    "\n\nChoose one from: literary fiction, sci-fi, fantasy, philosophy, biography, thriller, romance, academic writing, self-help, children's book, other. "
                    "Reply with only: genre: [your_choice]"
                )
            }
        ],
        temperature=0.3
    )
    content = response.choices[0].message.content
    match = re.search(r"genre:\s*(.+)", content, re.IGNORECASE)
    return match.group(1).strip().lower() if match else "other"

def get_genre_guidance(genre: str) -> str:
    guidance_map = {
        "literary fiction": "Focus on subtle emotional tone, literary metaphors, and abstract expressions.",
        "sci-fi": "Explain technical or futuristic terms and unfamiliar concepts clearly.",
        "fantasy": "Clarify mythical elements, symbolic terms, or invented vocabulary.",
        "philosophy": "Emphasise logical structure, abstract concepts, and difficult sentence constructions.",
        "biography": "Focus on historical references and less common vocabulary.",
        "thriller": "Clarify idiomatic suspense language or psychological tension.",
        "romance": "Highlight emotional tone and cultural idioms.",
        "academic writing": "Explain formal constructions, logical connectors, and field-specific vocabulary.",
        "self-help": "Clarify abstract motivational language and practical expressions.",
        "children's book": "Add only minimal annotation — focus on occasionally unfamiliar terms.",
        "other": "Annotate as usual based on clarity and learner needs."
    }
    return guidance_map.get(genre, guidance_map["other"])

ANNOTATION_PROMPT_TEMPLATE_BASE = """Your role is to help me quickly and deeply understand English texts while improving my English skills.
Follow the guidelines below to carefully examine the entire text sentence by sentence and add annotations when needed.
Never skip or remove any part of the original text — even short lines or chapter titles like "Chapter no 8" must be preserved.
Read each sentence in context and add annotations in **simple English** only when needed.

📘 Genre-specific focus: {genre_guidance}

---

🔍 When to annotate:
- Annotate any sentence that contains words, grammar, or meaning that may be confusing or unfamiliar even for CEFR B2 level learners (intermediate English).
- Especially include vocabulary that is literary, uncommon, abstract, or emotional — even if it is not "very difficult".
- For example:
  - Emotional words (e.g., ache, tremble, haunted) or literary imagery
  - Abstract or metaphorical expressions (e.g., "his body is his again")
  - Long or grammatically complex sentences (e.g., omitted relative pronouns, inversion, causatives, subjunctive mood)
  - Subtle psychological changes or emotional tone
  - Important symbolic meaning in the story
  - Cultural references that may not be familiar to Japanese learners
  - Ambiguous idioms or logical implications

---

📝 Annotation style:

- Add footnote markers (e.g. [^1]) immediately after the word, phrase, or sentence that needs annotation.
- Write the footnote definitions at the end of the chunk using Obsidian-style syntax.
- Use emojis to indicate type:
  📚 (vocabulary), 💓 (emotion), 🔧 (grammar), 🗝️ (symbolism), 🇯🇵 (JP gloss),
  🧠 (idiom/nuance), 🌍 (culture), 🧩 (interpretation), ⏳ (tense/aspect), 📖 (literary device),
- Keep annotations short and simple. Do not use a polite or academic tone.
- 🇯🇵 Japanese definitions should be placed **after** the English explanation, and only when they provide helpful nuance or clarity.
- You may annotate words, expressions, or full sentences — based on learner value.
- Avoid annotating the same item more than once per chunk.

✅ Example:
He felt a strange ache[^1] in his chest.
...He tried to keep a straight face[^2], but his eyes betrayed him.
She sat in silence, staring at the floor.[^3]

[^1]: 📚 ache: dull, persistent pain  🇯🇵 うずくような痛み

[^2]: 🧠 keep a straight face: try not to show emotion, usually laughter or sadness

[^3]: 🧩 This sentence suggests emotional suppression or internal conflict

✍️ Text to annotate:

{chunk}
""".strip()

def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    paragraphs = re.split(r'\n\s*\n', text.strip())
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_words = para.split()
        if current_length + len(para_words) > chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(para)
        current_length += len(para_words)

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks

@retry()
def annotate_chunk_with_prompt(chunk: str, prompt_template: str) -> str:
    prompt = prompt_template.format(chunk=chunk)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful and skilled AI English coach. "
                    "Follow all instructions exactly. Use Obsidian-style footnotes. "
                    "Do not annotate the same word or phrase more than once per chunk."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    if not response.choices or not response.choices[0].message.content:
        raise RuntimeError("Empty response from OpenAI")
    return response.choices[0].message.content

def normalize_footnotes(text: str, start_number: int = 1) -> Tuple[str, int]:
    refs = REF_PATTERN.findall(text)
    defs = DEF_PATTERN.findall(text)

    mapping = {}
    counter = start_number

    for old_id in sorted(set(refs + defs), key=int):
        if old_id not in mapping:
            mapping[old_id] = str(counter)
            counter += 1

    for old, new in mapping.items():
        text = re.sub(rf"\[\^{old}\]:", f"[^{new}]:", text)
        text = re.sub(rf"\[\^{old}\](?!:)", f"[^{new}]", text)

    return text, counter

def process_file(file_path: str):
    input_path = Path(file_path)
    output_path = input_path.with_name(input_path.stem + "_annotated.txt")

    if output_path.exists():
        print(f"⚠️ Warning: {output_path.name} already exists. Overwriting.")

    input_text = input_path.read_text(encoding="utf-8")
    chunks = split_into_chunks(input_text)

    print("🔍 Detecting genre from intro...")
    genre = detect_genre_intro(input_text)
    guidance = get_genre_guidance(genre)
    print(f"📘 Detected genre: {genre}")
    print(f"🧭 Guidance: {guidance}")

    prompt_template = ANNOTATION_PROMPT_TEMPLATE_BASE.replace("{genre_guidance}", guidance)

    annotated_chunks = []
    footnote_counter = 1

    for i, chunk in enumerate(chunks):
        print(f"🔄 Processing chunk {i + 1}/{len(chunks)} ...")
        annotated = annotate_chunk_with_prompt(chunk, prompt_template)
        normalized, footnote_counter = normalize_footnotes(annotated, footnote_counter)
        annotated_chunks.append(normalized)

    output_path.write_text("\n\n".join(annotated_chunks), encoding="utf-8")
    print(f"✅ Annotated output saved to: {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to the input file")
    args = parser.parse_args()
    process_file(args.input_file)

if __name__ == "__main__":
    main()
