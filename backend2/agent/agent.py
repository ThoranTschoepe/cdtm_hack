from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import os
from werkzeug.utils import secure_filename
import base64
from agent_ocr import MultiDocumentProcessor  # Import your OCR processor

app = Flask(__name__)
app.secret_key = 'your-secret-key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the document processor
document_processor = MultiDocumentProcessor()

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

@app.route("/process_document", methods=["POST"])
def process_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
        
    # Save the file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Process the document
    try:
        with open(filepath, "rb") as f:
            image_bytes = f.read()
            
        # Process single image
        result = document_processor.process_pages([image_bytes])
        
        # Update state with extracted information
        state = session.get("state", {})
        
        # Extract relevant information based on document type
        extracted_data = extract_relevant_info(result)
        
        # Update session with extracted data
        if "extracted_documents" not in state:
            state["extracted_documents"] = []
            
        state["extracted_documents"].append({
            "filename": filename,
            "data": extracted_data,
            "document_types": list(result.document_groups.keys())
        })
        
        session["state"] = state
        
        return jsonify({
            "success": True,
            "filename": filename,
            "extracted_data": extracted_data,
            "document_types": list(result.document_groups.keys())
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract_relevant_info(result):
    """Extract relevant information from OCR result based on document type"""
    extracted_info = {}
    
    for doc_type, group in result.document_groups.items():
        if not group.combined_data:
            continue
            
        data = group.combined_data
        
        # Process based on document type
        if doc_type == "MedicationBox" or doc_type == "Prescription":
            medications = data.get("medications", [])
            if "medications" not in extracted_info:
                extracted_info["medications"] = []
            extracted_info["medications"].extend(medications)
            
        elif doc_type == "HospitalLetter" or doc_type == "DoctorLetter":
            # Extract diagnosis and hospital/clinic info
            if "diagnoses" in data:
                extracted_info["diagnoses"] = data.get("diagnoses", [])
            if "hospital" in data:
                extracted_info["hospital_visits"] = [data.get("hospital", {})]
                
        elif doc_type == "LabReport":
            if "test_results" in data:
                extracted_info["test_results"] = data.get("test_results", [])
                
        # Add patient info from any document type
        if "patient" in data:
            extracted_info["patient"] = data.get("patient", {})
    
    return extracted_info

# Modify the chat route to use extracted information
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
            "last_question": None,
            "extracted_documents": []
        }

    state = session["state"]
    message = ""
    done = False
    extracted_data_preview = None

    if request.method == "POST":
        # We upload a picture
        if state["awaiting_followup"]:
            file = request.files.get("file")
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                
                # Process the uploaded document with OCR
                try:
                    with open(path, "rb") as f:
                        image_bytes = f.read()
                        
                    # Process single image
                    result = document_processor.process_pages([image_bytes])
                    
                    # Extract relevant information based on document type
                    extracted_data = extract_relevant_info(result)
                    
                    # Preview for display
                    extracted_data_preview = extracted_data
                    
                    # Update current question based on extracted data
                    current_q = questions[state["current_q_index"]]
                    auto_answer = check_extracted_data_for_answer(current_q, extracted_data)
                    
                    # Update state with the answer and document
                    updateState(state, current_q, auto_answer or "yes", filename)
                    
                    # Add extracted data to state
                    if "extracted_documents" not in state:
                        state["extracted_documents"] = []
                        
                    state["extracted_documents"].append({
                        "filename": filename,
                        "data": extracted_data,
                        "document_types": list(result.document_groups.keys())
                    })
                    
                except Exception as e:
                    # If OCR fails, just treat as regular upload
                    updateState(state, state["last_question"], "yes", filename)
                    
                state["awaiting_followup"] = False
                state["current_q_index"] += 1
            else:
                updateState(state, state["last_question"], "yes", None)
                state["awaiting_followup"] = False
                state["current_q_index"] += 1
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

    # Enhanced template with document processing
    return render_template_string("""
        <html>
        <head>
            <title>Health Chat</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .chat-container { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
                .extracted-info { background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 10px; }
                .document-item { margin-bottom: 10px; }
                h4 { margin-bottom: 10px; }
                .file-upload { margin: 15px 0; }
                input[type="submit"] { background-color: #4CAF50; color: white; padding: 8px 15px; border: none; 
                                      border-radius: 4px; cursor: pointer; }
                input[type="text"] { padding: 8px; width: 70%; border: 1px solid #ddd; border-radius: 4px; }
                input[type="file"] { margin-bottom: 10px; }
                .history-item { margin-bottom: 8px; }
            </style>
        </head>
        <body>
            <h2>Medical Information Onboarding</h2>
            
            <div class="chat-container">
                <p><strong>Bot:</strong> {{ message }}</p>

                {% if not done %}
                    {% if state.awaiting_followup %}
                        <form method="post" enctype="multipart/form-data">
                            <div class="file-upload">
                                <p>Upload your medical document:</p>
                                <input type="file" name="file" accept="image/*,.pdf" required>
                                <input type="submit" value="Upload & Process">
                            </div>
                        </form>
                    {% else %}
                        <form method="post">
                            <input type="text" name="user_input" required autofocus placeholder="Type your answer...">
                            <input type="submit" value="Send">
                        </form>
                    {% endif %}
                {% else %}
                    <p>Conversation complete.</p>
                    <a href="{{ url_for('reset') }}">Restart</a>
                {% endif %}
            </div>

            {% if extracted_data_preview %}
            <div class="extracted-info">
                <h4>Extracted Information:</h4>
                <pre>{{ extracted_data_preview | tojson(indent=2) }}</pre>
            </div>
            {% endif %}
            
            <!-- Extracted Documents Summary -->
            {% if state.extracted_documents and state.extracted_documents|length > 0 %}
            <div class="extracted-info">
                <h4>Processed Documents:</h4>
                {% for doc in state.extracted_documents %}
                <div class="document-item">
                    <strong>{{ doc.filename }}</strong> ({{ doc.document_types|join(', ') }})
                    {% if doc.data.medications %}
                        <p>Medications: {{ doc.data.medications|map(attribute='name')|join(', ') }}</p>
                    {% endif %}
                    {% if doc.data.diagnoses %}
                        <p>Diagnoses: {{ doc.data.diagnoses|map(attribute='condition')|join(', ') }}</p>
                    {% endif %}
                    {% if doc.data.hospital_visits %}
                        <p>Hospitals: {{ doc.data.hospital_visits|map(attribute='name')|join(', ') }}</p>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <hr>
            <h4>Conversation History</h4>
            <ul>
                {% for entry in state.prevQuestions %}
                    <li class="history-item"><b>{{ entry.question }}</b>: {{ entry.answer }}
                        {% if entry.followup %}
                            <br><i>Uploaded file:</i> {{ entry.followup }}
                        {% endif %}
                    </li>
                {% endfor %}
            </ul>
        </body>
        </html>
    """, message=message, state=state, done=done, extracted_data_preview=extracted_data_preview)

def check_extracted_data_for_answer(question, extracted_data):
    """Check if the extracted data can answer the current question"""
    question_lower = question.lower()
    
    if "medication" in question_lower and extracted_data.get("medications"):
        return "yes - found in document: " + ", ".join(m.get("name", "") for m in extracted_data.get("medications", [])[:3])
        
    if "hospital" in question_lower and extracted_data.get("hospital_visits"):
        return "yes - found in document: " + extracted_data.get("hospital_visits", [{}])[0].get("name", "Hospital visit confirmed")
        
    if "chronic" in question_lower and "disease" in question_lower and extracted_data.get("diagnoses"):
        return "yes - found in document: " + ", ".join(d.get("condition", "") for d in extracted_data.get("diagnoses", [])[:3])
        
    return None

@app.route("/reset")
def reset():
    session.pop("state", None)
    return redirect(url_for("chat"))

if __name__ == "__main__":
    app.run(debug=True)