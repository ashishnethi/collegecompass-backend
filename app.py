from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

with open("universities.json", "r") as f:
    universities = json.load(f)

def generate_reason(user, uni):
    reasons = []
    
    if user["gmat"] >= uni["avg_gmat"]:
        reasons.append("You exceed the typical GMAT for this university.")
    elif user["gmat"] >= uni["avg_gmat"] - 30:
        reasons.append("Your GMAT is competitive for this program.")
    else:
        reasons.append("Admissions may be tough based on GMAT.")
    
    if user["gpa"] >= uni["avg_gpa"]:
        reasons.append("Your GPA matches or surpasses their average.")
    else:
        reasons.append("Lower GPA can be offset with a higher GMAT, outstanding work experience, or strong extracurriculars.")
    
    if user["exp"] >= uni["avg_exp"]:
        reasons.append("You have solid work experience for this program.")
    else:
        reasons.append("Gaining more work experience could improve admission odds.")
    
    if user["goal"] in uni["career_focus"]:
        reasons.append("Strong track record in your chosen career field.")
    else:
        reasons.append(f"{user['goal']} placements possible, but not the main focus here.")
    
    if user["budget"] >= uni["tuition"]:
        reasons.append("Fits comfortably within your stated budget.")
    else:
        reasons.append("This college is above your stated budget threshold.")
    
    roi = round(uni["avg_salary"] / uni["tuition"], 2)
    reasons.append(f"Estimated ROI after graduation: {roi}x.")
    return " ".join(reasons)

@app.route("/api/match", methods=["POST"])
def match():
    data = request.json
    gmat, gpa, exp = data.get("gmat"), data.get("gpa"), data.get("exp")
    goal, budget = data.get("goal"), data.get("budget")
    scored = []

    for uni in universities:
        gmat_score = max(0, 1 - abs(gmat - uni["avg_gmat"]) / 100)
        gpa_score = max(0, 1 - abs(gpa - uni["avg_gpa"]) / 1.2)
        exp_score = max(0, 1 - abs(exp - uni["avg_exp"]) / 5)
        career_score = 1.0 if goal in uni["career_focus"] else 0.7
        roi_score = min(uni["avg_salary"] / uni["tuition"], 3)
        roi_boost = 1.0 if budget >= uni["tuition"] else 0.75

        fit = (
            0.3 * gmat_score +
            0.2 * gpa_score +
            0.15 * exp_score +
            0.15 * career_score +
            0.2 * roi_score * roi_boost
        ) * 100
        fit = round(min(fit, 100), 2) 

        reason = generate_reason(data, uni)
        scored.append({
            "name": uni["name"],
            "region": uni["region"],
            "fit_score": fit,
            "roi": round(uni["avg_salary"] / uni["tuition"], 2),
            "reason": reason,
        })

    sorted_unis = sorted([u for u in scored if u["fit_score"] > 60], key=lambda x: -x["fit_score"])[:5]
    return jsonify(sorted_unis)

if __name__ == "__main__":
    app.run(debug=True)
