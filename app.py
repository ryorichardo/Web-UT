import os
from flask import *

app = Flask(__name__)



@app.route("/", methods = ['POST', 'GET'])
def index():

        
    return render_template("home.html")

# MAIN
if __name__ == "__main__":
    app.run(debug=True)
