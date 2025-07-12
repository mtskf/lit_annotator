<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/status-alpha-blue">
</p>

# lit_annotator

**lit_annotator** is a lightweight, no-frills tool for English learners—especially Japanese speakers—who want to deeply understand English texts with the help of GPT-powered **inline footnote annotations**.

It reads `.txt` files, splits them into ~600-word chunks, auto-detects the **genre**, applies genre-specific annotation guidance, and sends each chunk to GPT-4o to generate easy-to-understand annotations in **Obsidian-style footnotes**.

---

## ✨ What It Does

- Automatically detects the text's **genre** (e.g., literary fiction, fantasy, self-help)
- Applies **genre-specific annotation strategy**
- Adds annotations for:
  - 📚 Difficult or abstract vocabulary
  - 🔧 Complex grammar and syntax
  - 💓 Emotional nuance and tone
  - 🧠 Idioms or ambiguous expressions
  - 🗝️ Symbolism and metaphor
  - 🌍 Cultural references
  - 🧩 Subtle interpretation or logic
  - ⏳ Tense, mood, and aspect
  - 📖 Literary techniques or devices
  - 🇯🇵 Japanese glosses (when helpful)

- Outputs `.txt` files with **Obsidian-style** footnotes like:

```text
She kept her composure[^1] even as the storm raged outside.

[^1]: 🧠 keep one's composure: remain calm and in control  🇯🇵 平静を保つ
```

---

## 📌 Annotation Rules

- Footnotes use emoji markers for clarity:

| Emoji | Category          | Use Case                                |
|-------|-------------------|------------------------------------------|
| 📚    | Vocabulary         | Word definitions                         |
| 🔧    | Grammar            | Structure, syntax                        |
| 💓    | Emotion            | Feelings, emotional tone                 |
| 🧠    | Idiom/Nuance       | Phrases, unclear nuance                  |
| 🗝️     | Symbolism         | Metaphor, allegory, hidden meaning       |
| 🌍    | Culture            | Social/cultural context                  |
| 🧩    | Interpretation     | Psychological/implicit logic             |
| ⏳    | Tense/Aspect       | Tense, mood, aspect, subjunctive etc.    |
| 📖    | Literary Device    | Literary/rhetorical technique            |
| 🇯🇵    | JP Gloss           | Japanese gloss if helpful after English  |

---

## 🚀 Quickstart

```bash
# Clone this repo
git clone https://github.com/yourusername/lit_annotator.git
cd lit_annotator

# Optional: Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your OpenAI key to .env
echo "OPENAI_API_KEY=your_api_key" > .env

# Run the annotator on a text file
python -m lit_annotator your_text.txt
```

Output will be saved as `your_text_annotated.txt`.

---

## 🪪 License

MIT. Free to use, modify, and share. Contributions welcome!
