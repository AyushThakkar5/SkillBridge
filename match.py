from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/match-skills", methods=["POST"])
def match_skills():

    data = request.get_json()

    candidate = data.get("candidate", {})
    employer = data.get("employer", {})

    candidate_skills = set(skill.lower() for skill in candidate.get("skills", []))
    required_skills = set(skill.lower() for skill in employer.get("required_skills", []))

    if not required_skills:
        return jsonify({"error": "Employer required skills missing"}), 400

    matched_skills = candidate_skills.intersection(required_skills)

    match_percentage = (len(matched_skills) / len(required_skills)) * 100

    if match_percentage >= 70:
        return jsonify({
            "cuid": candidate.get("uid"),
            "cid": candidate.get("cid"),
            "cskills": list(candidate_skills),
            "euid": employer.get("uid"),
            "eid": employer.get("eid"),
            "match_percentage": round(match_percentage, 2)
        })

    return jsonify({
        "message": "Match below 70%",
        "match_percentage": round(match_percentage, 2)
    })