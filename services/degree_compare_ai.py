import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def compare_degrees(degree1, degree2):

    prompt = f"""
Compare

Degree 1 : {degree1}

Degree 2 : {degree2}

Return ONLY valid JSON.

Include ALL these sections.

{{
"Overview": {{
"{degree1}":"",
"{degree2}":""
}},

"Subjects": {{
"{degree1}":[...],
"{degree2}":[...]
}},

"Programming Languages": {{
"{degree1}":[...],
"{degree2}":[...]
}},

"Career Opportunities": {{
"{degree1}":[...],
"{degree2}":[...]
}},

"Higher Studies": {{
"{degree1}":[...],
"{degree2}":[...]
}},

"Average Salary": {{
"{degree1}":"₹X – ₹Y LPA",
"{degree2}":"₹X – ₹Y LPA"
}},

"Advantages": {{
"{degree1}":[...],
"{degree2}":[...]
}},

"Disadvantages": {{
"{degree1}":[...],
"{degree2}":[...]
}},

"Which Degree is Better": {{
"{degree1}":"",
"{degree2}":""
}},

"Final Recommendation":""
}}

IMPORTANT:
Always provide realistic average salary ranges in Indian LPA.
Never leave Average Salary empty.
"""

    response = model.generate_content(prompt)

    text = response.text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()

    data = json.loads(text)

    return {
    "overview": {
        "degree1": data["Overview"].get(degree1, ""),
        "degree2": data["Overview"].get(degree2, "")
    },

    "subjects": {
        "degree1": data["Subjects"].get(degree1, []),
        "degree2": data["Subjects"].get(degree2, [])
    },

    "languages": {
        "degree1": data["Programming Languages"].get(degree1, []),
        "degree2": data["Programming Languages"].get(degree2, [])
    },

    "career": {
        "degree1": data["Career Opportunities"].get(degree1, []),
        "degree2": data["Career Opportunities"].get(degree2, [])
    },

    "higher_studies": {
        "degree1": data["Higher Studies"].get(degree1, []),
        "degree2": data["Higher Studies"].get(degree2, [])
    },

    "salary": {
        "degree1": data["Average Salary"].get(degree1, ""),
        "degree2": data["Average Salary"].get(degree2, "")
    },

    "advantages": {
        "degree1": data["Advantages"].get(degree1, []),
        "degree2": data["Advantages"].get(degree2, [])
    },

    "disadvantages": {
        "degree1": data["Disadvantages"].get(degree1, []),
        "degree2": data["Disadvantages"].get(degree2, [])
    },

    "recommendation": {
        "best_for_coding": degree1,
        "best_for_ai": degree1,
        "best_salary": degree1,
        "best_overall": data.get("Final Recommendation", "")
    }
}