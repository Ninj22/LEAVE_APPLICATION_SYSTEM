from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
migrate = Migrate() 

__all__ = [
    'db','migrate', 'jwt', 'mail'
]