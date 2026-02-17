import io
import re
import docx2txt
from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
from skills_master import SKILLS_MASTER


app = Flask(__name__)
CORS(app)


# -------- TEXT EXTRACTION --------
def get_text_from_file(file):
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""

        for page in doc:
            text += page.get_text()

    elif filename.endswith(".docx"):
        text = docx2txt.process(file)

    else:
        raise ValueError("Only PDF or DOCX allowed.")

    return text.lower()


# -------- SKILL MATCHING --------
def extract_skills(text):

    # Clean text
    text = re.sub(r'\s+', ' ', text)

    found_skills = set()

    for skill in SKILLS_MASTER:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text):
            found_skills.add(skill)

    return list(found_skills)


# -------- API --------
@app.route("/extract-skills", methods=["POST"])
def extract_skills_api():

    if "resume" not in request.files:
        return jsonify({"error": "Upload file with key 'resume'"}), 400
    
    # return jsonify({"message": "API working"})


    file = request.files["resume"]

    try:
        text = get_text_from_file(file)
        skills = extract_skills(text)

        return jsonify({
            "skills": skills
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



