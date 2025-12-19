import time
import json
import os
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.errors import ServerError

client = genai.Client()


# -----------------------------------------------------------
#   SAVE GAME FUNCTION
# -----------------------------------------------------------

def save_game(correct_answer, ai_guess, was_correct, history):
    filename = "game_data.json"
    
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append({
        "correct_animal": correct_answer,
        "ai_guess": ai_guess,
        "was_correct": was_correct,
        "history": history,
        "timestamp": datetime.now().isoformat()
    })

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -----------------------------------------------------------
#   GENERATE QUESTION
# -----------------------------------------------------------

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

    for i in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an Akinator-style AI game. "
                        "Ask only clear yes/no/unknown questions about animals."
                    )
                )
            )
            return response.text.strip()

        except ServerError:
            time.sleep(2)

    return "I cannot generate a new question right now."


# -----------------------------------------------------------
#   MAKE GUESS
# -----------------------------------------------------------

def make_guess(history):
    history_json = json.dumps(history, ensure_ascii=False, indent=2)

    prompt = f"""
You have the following history of questions and answers (JSON):

{history_json}

Guess the animal the user is thinking of.
- Provide exactly one animal name.
- Do not explain your choice.
"""

    for i in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-1.0-pro",
                contents=prompt
            )
            return response.text.strip()

        except ServerError:
            print("Gemini overloaded, retrying...")
            time.sleep(2)

    return "I cannot make a guess right now."


# -----------------------------------------------------------
#   MAIN GAME LOOP
# -----------------------------------------------------------

def play():
    print("Think of an ANIMAL. I will try to guess it!\n")

    history = []
    MAX_QUESTIONS = 10

    # Start with a strong first question
    first_question = "Is it a mammal?"
    print("AI:", first_question)
    answer = input("Answer (yes/no/unknown): ").strip().lower()
    history.append({"question": first_question, "answer": answer})

    # Give server a little rest
    time.sleep(2)

    # Question loop
    while len(history) < MAX_QUESTIONS:
        question = generate_question(history)
        print("AI:", question)

        answer = input("Answer (yes/no/unknown): ").strip().lower()
        history.append({"question": question, "answer": answer})

        # Optional: could implement confidence check here
        # For now, we stop after max questions
        if len(history) >= MAX_QUESTIONS:
            break

    # Make the final guess
    guess = make_guess(history)
    print("\nI guess you are thinking of:", guess)

    confirm = input("Am I correct? (yes/no): ").strip().lower()

    if confirm == "yes":
        correct_answer = guess
        was_correct = True
        print("Yay! I got it right!")
    else:
        correct_answer = input("What animal were you thinking of? ").strip()
        was_correct = False
        print("Thanks! I will remember that.")

    save_game(
        correct_answer=correct_answer,
        ai_guess=guess,
        was_correct=was_correct,
        history=history
    )

    print("\nGame saved.\n")


# -----------------------------------------------------------
#   MAIN
# -----------------------------------------------------------

if __name__ == "__main__":
    play()
