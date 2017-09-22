from flask import Flask
app = Flask(__name__)
from application.my_flask_files import views
