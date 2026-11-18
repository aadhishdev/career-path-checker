import os
from flask import Flask, render_template, request, redirect, session, send_file
from pymongo import MongoClient

from services.pdf_reader import extract_text
from services.gemini_ai import analyze_resume
from services.degree_compare_ai import compare_degrees
from services.career_ai import career_advice    

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ----------------------------
# Flask App
# ----------------------------
app = Flask(__name__)
app.secret_key = "career_checker_secret"

UPLOAD_FOLDER = "static/uploads"
REPORT_FOLDER = "static/reports"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORT_FOLDER"] = REPORT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# ----------------------------
# MongoDB
# ----------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["career_checker"]
users = db["users"]

# ----------------------------
# Home
# ----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ----------------------------
# Login
# ----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = users.find_one({
            "email": email,
            "password": password
        })

        if user:
            session["user"] = user["name"]
            return redirect("/dashboard")

        return "Invalid Email or Password!"

    return render_template("login.html")


# ----------------------------
# Dashboard
# ----------------------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        username=session["user"]
    )


# ----------------------------
# Resume Upload
# ----------------------------
@app.route("/resume", methods=["GET", "POST"])
def resume():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        # Get selected job role
        job_role = request.form["job_role"]

        if "resume" not in request.files:
            return "No file selected."

        file = request.files["resume"]

        if file.filename == "":
            return "Please choose a PDF."

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file.filename
        )

        file.save(filepath)

        # Save filename in MongoDB
        users.update_one(
            {"name": session["user"]},
            {
                "$set": {
                    "resume": file.filename
                }
            }
        )

        # Extract Resume Text
        resume_text = extract_text(filepath)

        print("========== RESUME TEXT ==========")
        print(resume_text)
        print("=================================")

        # AI Analysis
        analysis = analyze_resume(
            resume_text,
            job_role
        )

        # Save in Session
        session["analysis"] = analysis
        session["job_role"] = job_role

        return render_template(
            "result.html",
            username=session["user"],
            job_role=job_role,
            analysis=analysis
        )

    return render_template("resume.html")


# ----------------------------
# Download PDF Report
# ----------------------------
@app.route("/download_report")
def download_report():
    

    if "analysis" not in session:
        return redirect("/resume")

    filename = f"{session['user']}_Resume_Report.pdf"

    filepath = os.path.join(
        app.config["REPORT_FOLDER"],
        filename
    )

    styles = getSampleStyleSheet()

    pdf = SimpleDocTemplate(filepath)

    story = []

    story.append(
        Paragraph(
            "<b>AI Resume Analysis Report</b>",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Candidate:</b> {session['user']}",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Target Job Role:</b> {session['job_role']}",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            session["analysis"].replace("\n", "<br/>"),
            styles["BodyText"]
        )
    )

    pdf.build(story)

    return send_file(
        filepath,
        as_attachment=True
    )
# ----------------------------
# Download Degree Comparison PDF
# ----------------------------
@app.route("/download_degree_report")
def download_degree_report():

    if "comparison" not in session:
        return redirect("/degree_compare")

    filename = "Degree_Comparison_Report.pdf"

    filepath = os.path.join(
        app.config["REPORT_FOLDER"],
        filename
    )

    styles = getSampleStyleSheet()
    pdf = SimpleDocTemplate(filepath)

    story = []

    story.append(
        Paragraph(
            "<b>AI Degree Comparison Report</b>",
            styles["Title"]
        )
    )

    comparison = session["comparison"]

    # Loop through all sections
    for section, value in comparison.items():

        story.append(
            Paragraph(f"<b>{section}</b>", styles["Heading2"])
        )

        if isinstance(value, dict):

            for degree, content in value.items():

                story.append(
                    Paragraph(f"<b>{degree}</b>", styles["Heading3"])
                )

                if isinstance(content, list):

                    for item in content:
                        story.append(
                            Paragraph("• " + str(item), styles["BodyText"])
                        )

                else:

                    story.append(
                        Paragraph(str(content), styles["BodyText"])
                    )

        else:

            story.append(
                Paragraph(str(value), styles["BodyText"])
            )

    pdf.build(story)

    return send_file(
        filepath,
        as_attachment=True
    )
# ----------------------------
# Register
# ----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if users.find_one({"email": email}):
            return "Email already exists!"

        users.insert_one({
            "name": name,
            "email": email,
            "password": password
        })

        return redirect("/login")

    return render_template("register.html")


# ----------------------------
# Logout
# ----------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

# ----------------------------
# Degree Comparison
# ----------------------------

@app.route("/degree_compare", methods=["GET", "POST"])
def degree_compare():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        degree1 = request.form["degree1"]
        degree2 = request.form["degree2"]

        comparison = compare_degrees(degree1, degree2)
        print(comparison)
        session["comparison"] = comparison
        return render_template(

        "compare_result.html",
        degree1=degree1,
        degree2=degree2,
        data=comparison
        )

    return render_template("degree_compare.html")

# ----------------------------
# AI Career Advisor
# ----------------------------
@app.route("/career_advisor", methods=["GET", "POST"])
def career_advisor():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        degree = request.form["degree"]
        skills = request.form["skills"]
        interests = request.form["interests"]

        result = career_advice(
            degree,
            skills,
            interests
        )

        session["career_result"] = result

        return render_template(
            "career_result.html",
            degree=degree,
            data=result
        )

    return render_template("career_advisor.html")


# ----------------------------
# Job Market
# ----------------------------
@app.route("/job_market")
def job_market():

    if "user" not in session:
        return redirect("/login")

    job_data = [

        # Artificial Intelligence
        {
            "role": "AI Engineer",
            "domain": "Artificial Intelligence",
            "demand": 92,
            "entry": "₹4–7 LPA",
            "mid": "₹8–15 LPA",
            "senior": "₹16–25 LPA"
        },
        {
            "role": "Machine Learning Engineer",
            "domain": "Artificial Intelligence",
            "demand": 89,
            "entry": "₹5–8 LPA",
            "mid": "₹9–17 LPA",
            "senior": "₹18–28 LPA"
        },

        # Software Development
        {
            "role": "Frontend Developer",
            "domain": "Software Development",
            "demand": 85,
            "entry": "₹3–6 LPA",
            "mid": "₹7–12 LPA",
            "senior": "₹13–22 LPA"
        },
        {
            "role": "Backend Developer",
            "domain": "Software Development",
            "demand": 88,
            "entry": "₹4–7 LPA",
            "mid": "₹8–14 LPA",
            "senior": "₹15–24 LPA"
        },
        {
            "role": "Full Stack Developer",
            "domain": "Software Development",
            "demand": 90,
            "entry": "₹4–8 LPA",
            "mid": "₹9–16 LPA",
            "senior": "₹17–28 LPA"
        },

        # Data
        {
            "role": "Data Analyst",
            "domain": "Data & Analytics",
            "demand": 84,
            "entry": "₹3–6 LPA",
            "mid": "₹7–12 LPA",
            "senior": "₹13–20 LPA"
        },
        {
            "role": "Data Scientist",
            "domain": "Data & Analytics",
            "demand": 87,
            "entry": "₹5–8 LPA",
            "mid": "₹9–17 LPA",
            "senior": "₹18–30 LPA"
        },

        # Cyber Security
        {
            "role": "Cyber Security Analyst",
            "domain": "Cyber Security",
            "demand": 82,
            "entry": "₹3–6 LPA",
            "mid": "₹7–13 LPA",
            "senior": "₹14–22 LPA"
        },

        # Cloud
        {
            "role": "Cloud Engineer",
            "domain": "Cloud Computing",
            "demand": 86,
            "entry": "₹4–7 LPA",
            "mid": "₹8–15 LPA",
            "senior": "₹16–26 LPA"
        },

        # DevOps
        {
            "role": "DevOps Engineer",
            "domain": "DevOps",
            "demand": 88,
            "entry": "₹4–8 LPA",
            "mid": "₹9–16 LPA",
            "senior": "₹17–27 LPA"
        }
    ]

    total_jobs = len(job_data)

    high_demand = len([
        job for job in job_data
        if job["demand"] >= 80
    ])

    top_demand = max(
        [job["demand"] for job in job_data],
        default=0
    )

    domains = len(set(
        job["domain"] for job in job_data
    ))

    return render_template(
        "job_market.html",
        job_data=job_data,
        total_jobs=total_jobs,
        high_demand=high_demand,
        top_demand=top_demand,
        domains=domains
    )
@app.route("/roadmap", methods=["GET", "POST"])
def roadmap():

    if "user" not in session:
        return redirect("/login")

    domains = {
        "Computer Science": [
            "Software Developer",
            "Full Stack Developer",
            "Web Developer",
            "Backend Developer",
            "Frontend Developer"
        ],

        "Artificial Intelligence": [
            "AI Engineer",
            "Machine Learning Engineer",
            "AI Developer",
            "Deep Learning Engineer"
        ],

        "Data Science": [
            "Data Scientist",
            "Data Analyst",
            "Data Engineer",
            "Business Intelligence Analyst"
        ],

        "Cybersecurity": [
            "Cybersecurity Analyst",
            "Security Engineer",
            "Ethical Hacker",
            "Penetration Tester"
        ],

        "Cloud Computing": [
            "Cloud Engineer",
            "Cloud Developer",
            "DevOps Engineer",
            "Cloud Architect"
        ],

        "Business Analytics": [
            "Business Analyst",
            "Business Intelligence Analyst",
            "Data Analyst"
        ],

        "Internet of Things": [
            "IoT Developer",
            "IoT Engineer",
            "Embedded Systems Engineer"
        ],

        "Software Testing": [
            "Software Tester",
            "QA Engineer",
            "Automation Tester"
        ]
    }

    selected_domain = request.args.get(
        "domain",
        "Computer Science"
    )

    selected_role = request.args.get(
        "role",
        "Software Developer"
    )

    roadmap_data = {

        "Computer Science": [
            (
                "Programming Basics",
                "Learn programming fundamentals, variables, loops, functions and problem solving."
            ),
            (
                "Data Structures",
                "Learn arrays, strings, linked lists, stacks, queues, trees and algorithms."
            ),
            (
                "Development Skills",
                "Learn software development tools, databases, Git and relevant technologies."
            ),
            (
                "Build Projects",
                "Create real-world projects related to your target software development role."
            ),
            (
                "Placement Preparation",
                "Practice coding, aptitude, technical interviews and communication."
            )
        ],

        "Artificial Intelligence": [
            (
                "Python Basics",
                "Learn Python programming, functions, libraries and problem solving."
            ),
            (
                "Mathematics",
                "Learn basic statistics, probability, linear algebra and mathematics used in AI."
            ),
            (
                "Machine Learning",
                "Learn supervised learning, unsupervised learning, model training and evaluation."
            ),
            (
                "AI Projects",
                "Build AI and machine learning projects using real-world datasets."
            ),
            (
                "AI Interview Preparation",
                "Practice machine learning concepts, coding, projects and technical interviews."
            )
        ],

        "Data Science": [
            (
                "Python and SQL",
                "Learn Python, SQL, data handling and basic programming concepts."
            ),
            (
                "Statistics",
                "Learn probability, statistics, data analysis and visualization."
            ),
            (
                "Data Analysis",
                "Learn Pandas, NumPy, data cleaning and visualization techniques."
            ),
            (
                "Machine Learning",
                "Learn machine learning algorithms and model evaluation."
            ),
            (
                "Data Science Projects",
                "Build practical data science projects using real datasets."
            )
        ],

        "Cybersecurity": [
            (
                "Computer Fundamentals",
                "Learn operating systems, computer networks and basic system concepts."
            ),
            (
                "Networking",
                "Learn TCP/IP, IP addressing, DNS, HTTP, firewalls and network security."
            ),
            (
                "Cybersecurity Basics",
                "Learn threats, vulnerabilities, malware, authentication and security controls."
            ),
            (
                "Ethical Hacking",
                "Learn penetration testing, vulnerability assessment and security tools."
            ),
            (
                "Security Projects",
                "Practice cybersecurity labs and build security-related projects."
            )
        ],

        "Cloud Computing": [
            (
                "Cloud Fundamentals",
                "Learn cloud computing concepts, service models and deployment models."
            ),
            (
                "Linux and Networking",
                "Learn Linux commands, networking and server fundamentals."
            ),
            (
                "Cloud Platform",
                "Learn cloud services, storage, databases, virtual machines and containers."
            ),
            (
                "DevOps",
                "Learn Git, CI/CD, Docker and deployment concepts."
            ),
            (
                "Cloud Projects",
                "Build and deploy applications using cloud technologies."
            )
        ],

        "Business Analytics": [
            (
                "Business Fundamentals",
                "Learn business concepts, problem solving and decision making."
            ),
            (
                "Excel and SQL",
                "Learn Excel, SQL and data manipulation techniques."
            ),
            (
                "Data Visualization",
                "Learn dashboards, charts and business reporting."
            ),
            (
                "Business Intelligence",
                "Learn BI tools and techniques for business decision making."
            ),
            (
                "Analytics Projects",
                "Build business analytics projects using real-world datasets."
            )
        ],

        "Internet of Things": [
            (
                "Programming Basics",
                "Learn C, Python and basic programming concepts."
            ),
            (
                "Electronics Basics",
                "Learn sensors, microcontrollers and basic electronic components."
            ),
            (
                "IoT Communication",
                "Learn networking, MQTT and communication between IoT devices."
            ),
            (
                "IoT Development",
                "Learn Arduino, ESP32 and other IoT development platforms."
            ),
            (
                "IoT Projects",
                "Build practical IoT projects using sensors and connected devices."
            )
        ],

        "Software Testing": [
            (
                "Testing Fundamentals",
                "Learn software testing concepts, test cases and testing processes."
            ),
            (
                "Manual Testing",
                "Learn functional testing, regression testing and defect reporting."
            ),
            (
                "Automation Testing",
                "Learn automation testing concepts and testing frameworks."
            ),
            (
                "API Testing",
                "Learn API testing, HTTP requests and response validation."
            ),
            (
                "Testing Projects",
                "Practice testing real applications and prepare test reports."
            )
        ]
    }

    roadmap = roadmap_data.get(
        selected_domain,
        roadmap_data["Computer Science"]
    )

    roles = domains.get(
        selected_domain,
        domains["Computer Science"]
    )

    return render_template(
        "roadmap.html",
        domains=domains,
        selected_domain=selected_domain,
        selected_role=selected_role,
        roles=roles,
        roadmap=roadmap
    )
@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/login")

    return render_template("profile.html")

@app.route("/career-gap", methods=["GET", "POST"])
def career_gap():

    domain = ""
    role = ""
    resume_name = None
    resume_text = None

    current_skills = []
    required_skills = []
    missing_skills = []
    score = 0

    # Get logged-in user
    username = session.get("user")

    if username:

        # Find user in MongoDB
        user = users.find_one({"name": username})

        if user:

            # Get uploaded resume filename
            resume_name = user.get("resume")

            # Read resume
            if resume_name:

                resume_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    resume_name
                )

                if os.path.exists(resume_path):

                    try:
                        resume_text = extract_text(resume_path)

                    except Exception as e:
                        print("Resume reading error:", e)


    # When Analyze Career Gap is clicked
    if request.method == "POST":

        domain = request.form.get("domain", "")
        role = request.form.get("role", "")


    # =====================================================
    # SKILLS REQUIRED FOR EACH ROLE
    # =====================================================

    role_skills = {

        "Frontend Developer": [
            "HTML",
            "CSS",
            "JavaScript",
            "React.js",
            "Git"
        ],

        "Backend Developer": [
            "Python",
            "Java",
            "SQL",
            "REST API",
            "Node.js",
            "Git"
        ],

        "Full Stack Developer": [
            "HTML",
            "CSS",
            "JavaScript",
            "React.js",
            "Node.js",
            "Express.js",
            "MongoDB",
            "REST API",
            "Git"
        ],

        "Data Analyst": [
            "Python",
            "SQL",
            "Excel",
            "Statistics",
            "Power BI"
        ],

        "Data Scientist": [
            "Python",
            "SQL",
            "Statistics",
            "Machine Learning",
            "Pandas",
            "NumPy"
        ],

        "AI Engineer": [
            "Python",
            "Machine Learning",
            "Deep Learning",
            "AI",
            "Data Processing"
        ],

        "Machine Learning Engineer": [
            "Python",
            "Statistics",
            "Machine Learning",
            "Scikit-learn",
            "Model Deployment"
        ],

        "Cyber Security Analyst": [
            "Networking",
            "Linux",
            "Cyber Security",
            "Threat Analysis",
            "SIEM"
        ],

        "Cloud Engineer": [
            "Linux",
            "Networking",
            "AWS",
            "Azure",
            "Docker"
        ],

        "DevOps Engineer": [
            "Linux",
            "Git",
            "Docker",
            "CI/CD",
            "Cloud"
        ],

        "Software Developer": [
            "Programming",
            "Data Structures",
            "Database",
            "Git",
            "Problem Solving"
        ]
    }


    # =====================================================
    # GET REQUIRED SKILLS
    # =====================================================

    required_skills = role_skills.get(role, [])


    # =====================================================
    # CHECK RESUME FOR SKILLS
    # =====================================================

    if resume_text and required_skills:

        resume_lower = resume_text.lower()

        for skill in required_skills:

            if skill.lower() in resume_lower:

                current_skills.append(skill)

            else:

                missing_skills.append(skill)


        # =================================================
        # CALCULATE SCORE
        # =================================================

        if len(required_skills) > 0:

            score = round(
                (len(current_skills) / len(required_skills)) * 100
            )


    # =====================================================
    # SEND DATA TO HTML
    # =====================================================

    return render_template(
        "career_gap.html",
        domain=domain,
        role=role,
        resume_name=resume_name,
        resume_text=resume_text,
        current_skills=current_skills,
        required_skills=required_skills,
        missing_skills=missing_skills,
        score=score
    )
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)

