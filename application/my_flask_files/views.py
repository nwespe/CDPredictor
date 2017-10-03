import pandas as pd
from flask import render_template
from flask import request, redirect
from run_model import eval_risk

from my_flask_files import app  # in __init__.py file


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/input', methods=['GET', 'POST'])
def patient_input():
    return render_template('input.html')


@app.route('/output', methods=['POST'])
def patient_output():
    # pull patient info from input fields and store it
    albumin = request.args.get('albumin')
    weight = request.args.get('weight')
    # run user inputs through model
    chars, result = eval_risk(method='input', chars=(albumin, weight)) # main result returned by model
    if result == 0:
        risk = 'low'
        method = 'use current standard of care'
    if result == 1:
        risk = 'high'
        method = 'use advanced diagnostic method'
    return render_template('output.html',
                           tables=[chars[:16].to_html(classes='table'),
                                   chars[16:32].to_html(classes='table'),
                                   chars[32:48].to_html(classes='table'),
                                   chars[48:].to_html(classes='table')],
                           risk=risk, method=method)


@app.route('/profile_input', methods=['GET', 'POST'])
def profile_input():
    return render_template('profile_input.html')


@app.route('/profile_output', methods=['POST'])
def profile_select():
    hadm_id = request.args.get('hadm_id')
    print hadm_id
    risk, results = eval_risk(name=hadm_id)
    return render_template('profile_output.html',
                           table=results.to_html(header=False, classes='table'),
                           risk=risk)


@app.route('/slides')
def slides():
    return render_template('slides.html')