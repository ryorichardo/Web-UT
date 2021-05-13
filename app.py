import os
from flask import *

app = Flask(__name__)



@app.route("/", methods = ['POST', 'GET'])
def index():
    return render_template("home.html", home=True, about=False)

@app.route('/about')
def about():
    return render_template('about.html', home=False, about=True)

# MAIN
if __name__ == "__main__":
    app.run(debug=True)

# mantap
