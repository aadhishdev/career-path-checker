import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load Environment Variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load Gemini Model
model = genai.GenerativeModel("gemini-2.5-flash")


def analyze_resume(resume_text, job_role):

    prompt = f"""
You are a professional ATS Resume Analyzer.

The candidate is applying for the following job role:

{job_role}

Analyze ONLY the information that is explicitly written in the resume.

STRICT RULES:

1. Use ONLY the exact information written in the resume.
2. Never infer, assume, or guess anything.
3. Never invent skills, technologies, projects, certifications, internships, achievements, or experience.
4. Never expand abbreviations.
5. If the resume says "MERN Stack", DO NOT list MongoDB, Express.js, React.js, or Node.js unless those words are explicitly written.
6. Compare the resume ONLY with the selected job role.
7. Mention Missing Skills only if they are commonly required for the selected job role.
8. Return plain text only.
9. Do NOT use Markdown formatting like ###, **, ##, ---, or *.

IMPORTANT:

If a technology is NOT literally written in the resume,
DO NOT mention it anywhere.

If a project is NOT written in the resume,
DO NOT mention it.

If a certification is NOT written in the resume,
DO NOT mention it.

If an internship is NOT written in the resume,
DO NOT mention it.

If a programming language or framework is NOT explicitly written,
DO NOT include it.

Never add information from your own knowledge.

Return exactly in this format:

Resume Score: xx/100

Target Job:
{job_role}

Skills Found:
- Skill 1
- Skill 2

Missing Skills:
- Skill 1
- Skill 2

Strengths:
- Point 1
- Point 2

Weaknesses:
- Point 1
- Point 2

Suggestions:
- Point 1
- Point 2

Resume:

{resume_text}
"""

    response = model.generate_content(prompt)
    
    return response.text
    