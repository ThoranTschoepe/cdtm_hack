# state:
# {meta: {name=""}, prevQuestions: [], diagnosis={}, current: {type: user | system, content: ""; signal: running | closing}}

questions = ["Do you take any medication", "Have you been to the hospital", "Do you have any chronic diseases"]

def nextQuestion(state, q):
    return q

def closeConversation(state):
    return "See you"

def sendMessage(state, text):
    print(text)

def getUserInput(state):
    return input("You: ")

# returns if a message is more a yes or a no
def contains(text, keyword):
    return keyword.lower() in text.lower()

def isPositive(state, text):
    if contains(text, "Yes"):
        return True
    else:
        return False

def getInputQuestion(state, q):
    return str("Do you have a report for the question: " + q + "?")

def updateState(state, x=None):
    # You can expand this to actually update diagnosis or other fields
    return state

def runChat():
    state = {
        "meta": {"name": ""},
        "prevQuestions": [],
        "diagnosis": {},
        "current": {"type": "user", "content": "", "signal": "running"}
    }

    for q in questions:
        while True:
            question = nextQuestion(state, q)

            if question is None:
                sendMessage(closeConversation(state))
                return

            sendMessage(state, question)
            answer = getUserInput(state)

            if isPositive(state, answer):
                inputQuestion = getInputQuestion(state, q)
                sendMessage(state, inputQuestion)
                responds = getUserInput(state)
                state = updateState(state)
            else:
                break

# Start the chat
runChat()
