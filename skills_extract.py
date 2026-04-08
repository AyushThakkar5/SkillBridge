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

@app.route("/match-skills", methods=["POST"])
def match_skills():
    try:
        data = request.get_json()

        candidates = data.get("candidate", [])
        employer = data.get("employer", {})

        # Required skills (send back as-is)
        required_skills = [skill.lower() for skill in employer.get("required_skills", [])]
        if not required_skills:
            return jsonify({"error": "Employer required skills missing"}), 400

        job_id = employer.get("jid")
        employer_id = employer.get("eid")

        if not job_id or not employer_id:
            return jsonify({"error": "Job ID or Employer ID missing"}), 400

        matched_candidates = []

        for candidate_data in candidates:
            candidate_skills = set(skill.lower() for skill in candidate_data.get("skills", []))
            candidate_id = candidate_data.get("cid")

            if not candidate_id:
                continue

            matched_skills = candidate_skills.intersection(required_skills)
            match_percentage = (len(matched_skills) / len(required_skills)) * 100

            if match_percentage >= 30:
                matched_candidates.append({
                    "cid": candidate_id,
                    "cskills": list(candidate_skills),
                    "jid": job_id,
                    "eid": employer_id,
                    "match_percentage": round(match_percentage, 2),
                    "matched_skills": list(matched_skills)
                })

        return jsonify({
            "matched_candidates": matched_candidates,
            "required_skills": required_skills,  # changed
            "total_matched": len(matched_candidates)
        })

    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500
from flask import Flask, request, jsonify

@app.route("/match-updated-candidate", methods=["POST"])
def match_updated_candidate():
    try:
        data = request.get_json()

        candidate = data.get("candidate", {})
        employers = data.get("employers", [])

        # Validation
        if not candidate or not employers:
            return jsonify({"error": "Candidate or employers data missing"}), 400

        candidate_id = candidate.get("cid")
        candidate_skills = set(
            skill.lower() for skill in candidate.get("skills", [])
        )

        if not candidate_id:
            return jsonify({"error": "Candidate ID missing"}), 400

        matched_candidates = []

        #  Loop through ALL jobs
        for employer in employers:

            required_skills = [
                skill.lower() for skill in employer.get("required_skills", [])
            ]

            if not required_skills:
                continue

            job_id = employer.get("jid")
            employer_id = employer.get("eid")

            if not job_id or not employer_id:
                continue

            #  Matching logic
            matched_skills = candidate_skills.intersection(required_skills)

            match_percentage = (len(matched_skills) / len(required_skills)) * 100

            if match_percentage >= 30:
                matched_candidates.append({
                    "cid": candidate_id,
                    "cskills": list(candidate_skills),
                    "jid": job_id,
                    "eid": employer_id,
                    "match_percentage": round(match_percentage, 2),
                    "matched_skills": list(matched_skills),

                    #  IMPORTANT FIX (for Node + Mongo validation)
                    "required_skills": required_skills
                })

        return jsonify({
            "matched_candidates": matched_candidates,
            "total_matched": len(matched_candidates)
        })

    except Exception as e:
        return jsonify({
            "error": f"Processing failed: {str(e)}"
        }), 500