from flask import Flask, request, render_template_string, redirect, url_for, session
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Questions
questions = ["Do you take any medication?", "Have you been to the hospital?", "Do you have any chronic diseases"]

# Logic
def nextQuestion(state, q):
    return q

def closeConversation(state):
    return "See you"

def sendMessage(state, text):
    print(text)

def contains(text, keyword):
    return keyword.lower() in text.lower()

def isPositive(state, text):
    return contains(text, "yes")

def getInputQuestion(state, q):
    return "Do you have a report for the question: " + q + "?"

def updateState(state, question=None, answer=None, followup_file=None):
    state["prevQuestions"].append({
        "question": question,
        "answer": answer,
        "followup": followup_file
    })
    return state

# UI + Logic Routing
@app.route("/", methods=["GET", "POST"])
def chat():
    if "state" not in session:
        session["state"] = {
            "meta": {"name": ""},
            "prevQuestions": [],
            "diagnosis": {},
            "current": {"type": "user", "content": "", "signal": "running"},
            "current_q_index": 0,
            "awaiting_followup": False,
            "last_question": None
        }

    state = session["state"]
    message = ""
    done = False

    if request.method == "POST":
        # We upload a picture
        if state["awaiting_followup"]:
            file = request.files.get("file")
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                updateState(state, state["last_question"], "yes", filename)
            else:
                updateState(state, state["last_question"], "yes", None)
            state["awaiting_followup"] = False
        else:
            user_input = request.form.get("user_input", "")
            current_q = questions[state["current_q_index"]]

            if isPositive(state, user_input):
                message = getInputQuestion(state, current_q)
                state["awaiting_followup"] = True
                state["last_question"] = current_q
            else:
                updateState(state, current_q, "no", None)
                state["current_q_index"] += 1

    if state["current_q_index"] >= len(questions):
        message = closeConversation(state)
        done = True
    elif not state["awaiting_followup"]:
        message = questions[state["current_q_index"]]

    session["state"] = state

    return render_template_string("""
        <html>
        <head><title>Health Chat</title></head>
        <body>
            <h2>Chat with HealthBot</h2>
            <p><strong>Bot:</strong> {{ message }}</p>

            {% if not done %}
                {% if state.awaiting_followup %}
                    <form method="post" enctype="multipart/form-data">
                        <input type="file" name="file" required>
                        <input type="submit" value="Upload">
                    </form>
                {% else %}
                    <form method="post">
                        <input type="text" name="user_input" required autofocus>
                        <input type="submit" value="Send">
                    </form>
                {% endif %}
            {% else %}
                <p>Conversation complete.</p>
                <a href="{{ url_for('reset') }}">Restart</a>
            {% endif %}

            <hr>
            <h4>Conversation History</h4>
            <ul>
                {% for entry in state.prevQuestions %}
                    <li><b>{{ entry.question }}</b>: {{ entry.answer }}
                        {% if entry.followup %}
                            <br><i>Uploaded file:</i> {{ entry.followup }}
                        {% endif %}
                    </li>
                {% endfor %}
            </ul>
        </body>
        </html>
    """, message=message, state=state, done=done)

@app.route("/reset")
def reset():
    session.pop("state", None)
    return redirect(url_for("chat"))

if __name__ == "__main__":
    app.run(debug=True)
