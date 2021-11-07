from flask import Flask, request, render_template

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/asses', methods =["GET", "POST"])
def assess():
    if request.method == "POST":
        # TODO - health function
        input1 = request.form['input1']
        # data = health(input1)
        data = "filler"
        # TODO - recommend exercises
        # exercise = exercise(data)
        return render_template('results.html', data = data, exercise = exercise)
    else:
        return render_template("search.html")

@app.route('/chatbot')
def bot():
    if request.method == "POST":
        output = chatbot(input)
    return render_template('Table/Table.html')

if __name__ == "__main__":
    app.run(debug = True)