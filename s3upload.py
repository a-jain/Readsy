import flask_s3
from application import application

flask_s3.create_all(application)