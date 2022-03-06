import os
import uuid

class Config(object):
    TESTING = False
    SECRET_KEY = str(uuid.uuid4())

class Development(Config):
    DATABASE_TYPE = "sqlite"
    DATABASE_URL = "/tmp/auth_system.db"
    JWT_SECRET = "s3cr3t"
    
class Testing(Config):
    TESTING = True
    DATABASE_TYPE = "sqlite"
    DATABASE_URL = "sqlite:///:memmory:"
    JWT_SECRET = "s3cr3t"
    
class Production(Config):
    DATABASE_TYPE = os.environ.get("DATABASE_TYPE")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET = os.environ.get("JWT_SECRET")

config = {
    "development": Development,
    "testing": Testing,
    "production": Production
}