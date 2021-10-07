from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from EcommerceStore.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "users.sign_in"
login_manager.login_message_category = "info"

def create_app(config_file=Config):
    app = Flask(__name__)
    app.config.from_object(config_file)
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from EcommerceStore.main.routes import main
    from EcommerceStore.carts.routes import carts
    from EcommerceStore.products.routes import products
    from EcommerceStore.users.routes import users
    from EcommerceStore.errors.handlers import errors

    app.register_blueprint(main)
    app.register_blueprint(carts)
    app.register_blueprint(products)
    app.register_blueprint(users)
    app.register_blueprint(errors)
    
    return app