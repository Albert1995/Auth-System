from flask import Flask

class DatabaseManager(object):
    
    def __init__(self, app: Flask = None) -> None:
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app

    def create_connection(self):
        if not self.app.config["DATABASE_TYPE"] or not self.app.config["DATABASE_URL"]:
            raise Exception("DATABASE_TYPE and DATABASE_URL are not defined. Please check your flask configuration")
        
        if self.app.config["DATABASE_TYPE"] == "sqlite":
            import sqlite3
            conn = sqlite3.connect(self.app.config["DATABASE_URL"])
            return conn
        elif self.app.config["DATABASE_TYPE"] == "postgres":
            import psycopg2
            conn = psycopg2.connect(self.app.config["DATABASE_URL"])
            return conn
        else:
            raise Exception(f"Unrecognized '{self.app.config['DATABASE_TYPE']}' database type")

    @property
    def wildcard(self):
        if self.app.config["DATABASE_TYPE"] == "sqlite":
            return "?"
        elif self.app.config["DATABASE_TYPE"] == "postgres":
            return "%s"
        return "?"
