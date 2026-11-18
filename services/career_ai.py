import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def career_advice(degree, skills, interests):

    prompt = f"""
You are an AI Career Advisor.

Student Degree:
{degree}

Skills:
{skills}

Interests:
{interests}

Return ONLY valid JSON.

{{
    "career_roles": [
        "Role 1",
        "Role 2",
        "Role 3",
        "Role 4",
        "Role 5"
    ],

    "required_skills":[
        "...",
        "...",
        "..."
    ],

    "certifications":[
        "...",
        "...",
        "..."
    ],

    "roadmap":[
        "Step 1",
        "Step 2",
        "Step 3",
        "Step 4"
    ],

    "salary":"₹X - ₹Y LPA",

    "top_companies":[
        "...",
        "...",
        "..."
    ],

    "future_scope":"...",

    "final_advice":"..."
}}

Only return JSON.
"""

    response = model.generate_content(prompt)

    text = response.text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)