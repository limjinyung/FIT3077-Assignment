import os
from flask import Flask
from online_matching_system.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    from online_matching_system.users.routes import users
    from online_matching_system.bids.routes import bids
    from online_matching_system.main.routes import main
    app.register_blueprint(users)
    app.register_blueprint(bids)
    app.register_blueprint(main)

    return app

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'c36daf1336f217b053880cd09aeebd54'
# app.static_folder = 'static'

# from online_matching_system import routes