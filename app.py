from flask import Flask, request, render_template
import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import pickle
import openai

openai.api_key = ''
completion = openai.Completion()

app = Flask(__name__, static_url_path='/static')

load_dotenv()

# ML
def heartrate(VO2):
    heartrate_model = pickle.load(open('heartrate.sav', 'rb'))
    heartrate = heartrate_model.predict([[VO2]]) # Predict heart rate
    message = ''
    exercise = []
    output = ''
    risk = ''
    recommendation = []
    learn_more ='https://www.nasa.gov/mission_pages/station/research/station-science-101/cardiovascular-health-in-microgravity/'

    if heartrate < 40:
        message=  'Your heartrate is low: ' + str(heartrate[0][0])[:3] + ' (b/min)'
        exercise.append('Advanced Resistive Exercise Device (ARED)')
        exercise.append('treadmill')
        exercise.append('stationary bike')
        recommendation.append('wear special trousers that use pressure differences to pull blood back into the abdomen and legs.')
        risk = 'hearing loss, brain edema and deformation of the eye known as Spaceflight Associated     Neuro-ocular Syndrome (SANS).'

    elif heartrate > 90:
        message = 'Your heartrate is high: ' + str(heartrate[0][0])[:3] + ' (b/min)'
        exercise.append('Advanced Resistive Exercise Device (ARED)')
        exercise.append('treadmill')
        exercise.append('stationary bike')
        risk = 'hearing loss, brain edema and deformation of the eye known as Spaceflight Associated     Neuro-ocular Syndrome (SANS).'
    else:
        message = 'Your heartrate is normal: '+ str(heartrate[0][0])[:3] + ' (b/min)'

    return {"message": message, "exercises": exercise, "recs": recommendation, "link": learn_more, "risk": risk}

def treadmill(initial_calf_muscle_volume):
    calf_muscle_loss_model = pickle.load(open('calf_muscle_loss.sav', 'rb'))
    calf_muscle_loss = calf_muscle_loss_model.predict([[initial_calf_muscle_volume]])
    calf_muscle_loss = calf_muscle_loss[0][0]
    treadmill_time_model = pickle.load(open('treadmill.sav', 'rb'))
    treadmill_time = calf_muscle_loss_model.predict([[calf_muscle_loss]])
    treadmill_time = treadmill_time[0][0]

    message = ''
    exercise = 'treadmill'

    learn_more ='https://www.nasa.gov/mission_pages/station/research/station-science-101/bone-muscle-loss-in-microgravity/'
    message = 'The loss of calf muscle is ' + str(calf_muscle_loss)[:5] + ' cm3 and we recommend you to exercise using the treadmill for ' + str(treadmill_time)[:3] + ' minutes per week.'

    return {"message": message, "exercises": exercise, "link": learn_more}

# OpenAI chatbot
start_chat_log = '''Human: Hello, who are you?
AI: I am doing great. How can I help you today?
'''
i = 0
def ask(question, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    prompt = f'{chat_log}Human: {question}\nAI:'
    response = completion.create(
        prompt=prompt, engine="davinci", stop=['\nHuman'], temperature=0.9,
        top_p=1, frequency_penalty=0, presence_penalty=0.6, best_of=1,
        max_tokens=150)
    answer = response.choices[0].text.strip()
    return answer

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    return f'{chat_log}Human: {question}\nAI: {answer}\n'
chat_log = start_chat_log

def final_function(user_input):
    global chat_log
    output = ask(user_input, chat_log)
    chat_log = append_interaction_to_chat_log(user_input, output, chat_log )
    return output

def chatbot(msg):
    return final_function(msg)

account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

# Flask app
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assess', methods =["GET", "POST"])
def assess():
    if request.method == "POST":
        calf = request.form['calf']
        vo2 = request.form['vo2']
        # return {"message": message, "exercises": exercise, "recs": recommendation, "link": learn_more, "risk": risk}
        vo2_results = heartrate(vo2)
        # return {"message": message, "exercises": exercise, "link": learn_more}
        treadmill_results = treadmill(calf)
        return render_template('results.html', vo2_message = vo2_results['message'],  vo2_exercise = vo2_results['exercises'], vo2_recs = vo2_results['recs'], vo2_link = vo2_results['link'], vo2_risk = vo2_results['risk'],treadmill_message = treadmill_results['message'], treadmill_exercise = treadmill_results['exercises'], treadmill_link = treadmill_results['link'])
    else:
        return render_template("assess.html")

@app.route('/get', methods=["POST"])
def get():
    msg = request.form['input']
    data = chatbot(msg)
    return data

# Twilio
def respond(message):
    response = MessagingResponse()
    response.message(message)
    return str(response)

@app.route('/message', methods=['POST'])
def reply():
    message = request.form.get('Body').lower()
    if message:
        return respond(chatbot(message))