import os
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'c36daf1336f217b053880cd09aeebd54'
app.static_folder = 'static'

from online_matching_system import routes