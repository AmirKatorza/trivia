import requests as r
import json


def load_questions_from_web():

    questions = {}
    
    response = r.get("https://opentdb.com/api.php?amount=50&type=multiple")

    # Try parsing the response as JSON
    try:
        data = response.json()  # This already returns a dictionary (or list)
        for question_no, question in enumerate(data["results"], start=1):
            questions[question_no] = {
                "question": question["question"],
                "answers": question["incorrect_answers"],
                "correct": question["correct_answer"]}
        
    except ValueError:
        print("Response is not in JSON format")
    
    return questions
