
from flask import Flask, render_template, request, url_for, send_file
import numpy as np
import pandas as pd
import pickle
import pymysql as mdb
import json
from sklearn.externals import joblib

app = Flask(__name__)


@app.route("/")
def d7():
    return render_template('index.html', start=True, found=True)

@app.route("/", methods=['POST'])
def d7_post():
    
    if 'search' in request.form:
        search_input = request.form['search'].lower()

    if search_input == '':
        search_input = 'Boston'.lower()

    if 'map.x' in request.form:
        x_in = request.form['map.x']
        y_in = request.form['map.y']
    else:
        x_in = 0
        y_in = 0

    lng_in = x_in
    lat_in = y_in
        
    found = True
    
    if found == False:
        return render_template('index.html',start=False,found=False)
    else:
        return render_template('index.html',start=False,found=True,
                               search_input=search_input,
                               lng_in=lng_in,lat_in=lat_in)

if __name__ == '__main__':
    app.run(debug=True)
