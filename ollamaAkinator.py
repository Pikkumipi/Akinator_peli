import json
import os
import time
from datetime import datetime
from openai import OpenAI

# -------------------------------
# OLLAMA CLIENT
# -------------------------------
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# -------------------------------
# MODELS
# -------------------------------
LLM_MODEL = "qwen2.5:7b-instruct"
DATA_FILE = "game_data.json"

TOTAL_QUESTIONS = 12  # <-- ALWAYS ASK EXACTLY 12 QUESTIONS

# -------------------------------
# UTILS
# -------------------------------
def normalize_answer(ans):
    ans = ans.strip().lower()
    if ans in ["k", "kyllä", "yes", "y"]:
        return "yes"
    if ans in ["e", "ei", "no", "n"]:
        return "no"
    return "unknown"

# -------------------------------
# STORAGE
# -------------------------------
def load_games():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_game(game):
    data = load_games()
    data.append(game)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------------------
# QUESTION GENERATION
# -------------------------------
def generate_question(history):
    history_json = json.dumps(history, ensure_ascii=False, indent=2)

    prompt = f"""
You are playing an Akinator-style game. The user is thinking of an ANIMAL.

History of previous questions and answers (JSON format):

{history_json}

Task:
- Ask one yes/no/unknown question that helps narrow down the animal.
- Focus on biological traits, habitat, size, diet, or distinctive features.
- Do not repeat previous questions.
- Make the question short and clear, exactly one sentence.
- Return ONLY the question.
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You ask optimal Akinator questions about animals."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

# -------------------------------
# MAKE GUESS
# -------------------------------
def make_guess(history):
    history_json = json.dumps(history, ensure_ascii=False, indent=2)

    prompt = f"""
You have the following history of questions and answers (JSON):

{history_json}

Guess the animal the user is thinking of.
- Provide exactly one animal name.
- Do not explain your choice.
- Provide exactly ONE word or name
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()

# -------------------------------
# MAIN GAME
# -------------------------------
def play():
    print("\nThink of an ANIMAL. I will ask 12 questions and then guess.\n")
    history = []

    # --- Question 1 ---
    q = "Is it a mammal?"
    print("AI:", q)
    ans = normalize_answer(input("Answer (yes/no/unknown): "))
    history.append({"question": q, "answer": ans})
    time.sleep(0.5)

    # --- Questions 2–12 ---
    while len(history) < TOTAL_QUESTIONS:
        q = generate_question(history)
        print("AI:", q)

        ans = normalize_answer(input("Answer (yes/no/unknown): "))
        history.append({"question": q, "answer": ans})
        time.sleep(0.5)

    # --- Guess ---
    guess = make_guess(history)
    print("\n🤔 My guess:", guess)

    correct = normalize_answer(input("Am I correct? (yes/no): "))
    if correct == "yes":
        real = guess
        print("🎉 I win!")
    else:
        real = input("What animal were you thinking of? ").strip()
        print("Thanks! I will remember that.")

    save_game({
        "correct_animal": real,
        "ai_guess": guess,
        "history": history,
        "timestamp": datetime.now().isoformat()
    })

    print("\nGame saved.\n")

# -------------------------------
if __name__ == "__main__":
    play()
