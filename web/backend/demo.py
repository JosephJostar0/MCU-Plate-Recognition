from pydantic import BaseModel
from flask_openapi3 import Info, Tag
from flask_openapi3 import OpenAPI
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import session

info = Info(title="book API", version="1.0.0")
app = OpenAPI(__name__, info=info)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.sqlite3'
db:SQLAlchemy = SQLAlchemy(app)

book_tag = Tag(name="book", description="Some Book")

# const class
class Administrator:
    @staticmethod
    def getAdmin():
        ADMIN = 'admin'
        PASSWORD = '10086'
        return ADMIN, PASSWORD
        
    @staticmethod
    def isAdmin(uname:str, pwd:str) -> bool:
        return (uname, pwd) == Administrator.getAdmin() 

# db Models
class Plate(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(16), unique=True, nullable=False)
    access = db.Column(db.Boolean, default=False)
    period = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self) -> str:
        return rf'Plate License: {self.number}'

# request models
class Book(BaseModel):
    age: int
    author: str

# @app.post("/book", summary="get books", tags=[book_tag])
@app.post("/book")
def get_book(body: Book):
    """
    to get all books
    """
    return {
        "code": 0,
        "message": "ok",
        "data": [
            {"bid": 1, "age": body.age, "author": body.author},
            {"bid": 2, "age": body.age, "author": body.author}
        ]
    }

def main():
    with app.app_context():
        db.create_all()
    app.run(debug=True)

if __name__ == "__main__":
    main()
