from flask import Flask, render_template, request, redirect, url_for, session
from questions import QUESTIONS
import random

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key"

QUESTIONS_PER_TEST = 10


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start_test():
    difficulty = request.form.get("difficulty", "Mixed")

    # Copy the question bank so we don't modify the original.
    available = QUESTIONS.copy()

    if difficulty != "Mixed":
        available = [
            q for q in available
            if q["difficulty"] == difficulty
        ]

    if len(available) < QUESTIONS_PER_TEST:
        return (
            f"Not enough questions for {difficulty}. "
            "Add more questions to questions.py.",
            400
        )

    selected = random.sample(available, QUESTIONS_PER_TEST)

    # Store answers on the server, not in the browser.
    session["quiz"] = [
        {
            "id": q["id"],
            "answer": q["answer"],
            "points": q.get("points", 1),
            "difficulty": q["difficulty"],
            "category": q["category"],
            "explanation": q["explanation"],
            "question": q["question"],
            "options": q["options"],
        }
        for q in selected
    ]

    session["difficulty"] = difficulty
    session["started"] = True

    return redirect(url_for("quiz"))


@app.route("/quiz")
def quiz():
    quiz_data = session.get("quiz")

    if not quiz_data or not session.get("started"):
        return redirect(url_for("home"))

    # Send only the question and options to the page.
    public_questions = [
        {
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "category": q["category"],
            "difficulty": q["difficulty"],
        }
        for q in quiz_data
    ]

    return render_template("quiz.html", questions=public_questions)


@app.route("/submit", methods=["POST"])
def submit():
    quiz_data = session.get("quiz")

    if not quiz_data or not session.get("started"):
        return redirect(url_for("home"))

    correct = 0
    total_points = 0
    earned_points = 0
    review = []
    category_stats = {}
    difficulty_stats = {}

    for q in quiz_data:
        total_points += q["points"]

        submitted = request.form.get(str(q["id"]), "")
        is_correct = submitted == str(q["answer"])

        if is_correct:
            correct += 1
            earned_points += q["points"]

        review.append({
            "question": q["question"],
            "options": q["options"],
            "chosen": submitted,
            "answer": str(q["answer"]),
            "correct": is_correct,
            "explanation": q["explanation"],
            "category": q["category"],
            "difficulty": q["difficulty"],
        })

        for stats, key in [
            (category_stats, q["category"]),
            (difficulty_stats, q["difficulty"]),
        ]:
            if key not in stats:
                stats[key] = {"correct": 0, "total": 0}

            stats[key]["total"] += 1

            if is_correct:
                stats[key]["correct"] += 1

    accuracy = round((correct / len(quiz_data)) * 100) if quiz_data else 0
    weighted_score = (
        round((earned_points / total_points) * 100)
        if total_points else 0
    )

    session["started"] = False


    # Informal IQ-style estimate — not a validated IQ score
    score_for_estimate = max(0, min(100, weighted_score))
    iq_estimate = round(70 + (score_for_estimate / 100) * 60)

    return render_template(
        "results.html",
        correct=correct,
        total=len(quiz_data),
        accuracy=accuracy,
        weighted_score=weighted_score,
        iq_estimate=iq_estimate,
        review=review,
        category_stats=category_stats,
        difficulty_stats=difficulty_stats,
    )


if __name__ == "__main__":
    app.run(debug=True)