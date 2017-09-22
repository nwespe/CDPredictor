from flask import render_template
from flask import request

from application.my_flask_files import app  # in __init__.py file
from application.run_model import eval_risk


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/input', methods=['POST'])
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


@app.route('/profile_output', methods=['POST'])
def patient_select():
    chars, result = eval_risk(method='profile')
    chars = chars.transpose()
    if result == 0:
        risk = 'low'
        method = 'use current standard of care'
    if result == 1:
        risk = 'high'
        method = 'use advanced diagnostic method'
    return render_template('output.html', #dataframe=chars.to_html(classes='table'),
                           tables=[chars[:16].to_html(classes='table'),
                                   chars[16:32].to_html(classes='table'),
                                   chars[32:48].to_html(classes='table'),
                                   chars[48:].to_html(classes='table')],
                           risk=risk, method=method)
