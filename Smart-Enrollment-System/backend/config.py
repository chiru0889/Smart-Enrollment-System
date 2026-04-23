SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:mysql123@localhost/certisured_db"
SQLALCHEMY_TRACK_MODIFICATIONS = False


import os

class Config:
    SECRET_KEY = "analogica-secret-key"
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
