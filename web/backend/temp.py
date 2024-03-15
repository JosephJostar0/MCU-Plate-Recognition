from flask import Flask, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_restful_swagger import swagger
from datetime import datetime
import logging
import sys

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.WARNING)
logger.addHandler(handler)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.sqlite3'
db:SQLAlchemy = SQLAlchemy(app)
api = Api(app)
api = swagger.docs(api)

class Administrator:
    @staticmethod
    def getAdmin():
        ADMIN = 'admin'
        PASSWORD = '10086'
        return ADMIN, PASSWORD
        
    @staticmethod
    def isAdmin(uname:str, pwd:str) -> bool:
        return (uname, pwd) == Administrator.getAdmin() 

# Create Models 
class Plate(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(16), unique=True, nullable=False)
    access = db.Column(db.Boolean, default=False)
    period = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self) -> str:
        return rf'Plate License: {self.number}'

# web
class UserLogin(Resource):
    @swagger.operation()
    def post(self):
        userName = request.json.get('username')
        password = request.json.get('password')
        if Administrator.isAdmin(userName, password):
            session['username'] = userName
            return jsonify({'message':'Login succefful'})
        else:
            return jsonify({'message': 'Invalid username or passowrd'}), 401

class UserLogout(Resource):
    @swagger.operation()
    def post(self):
        if 'username' in session:
            session.pop('username')
            return jsonify({'message': 'Logout successful'})
        else:
            return jsonify({'message': 'No active session'}), 401

class PlateInfo(Resource):
    @swagger.operation(
        notes='get plateInfo by id',
        responseClass=str,
        nickname='getPlateInfo',
        parameters=[
            {
                "name":"pid",
                "description": "primary key of plate",
                "required":True,
                "allowMultiple": False,
                "dataType":"int",
                "paramType":"form",
            }
        ]
    )
    def post(self):
        pid:int = request.form.get('pid')
        
        plate:Plate = Plate.query.filter_by(pid=pid).first()
        if plate:
            return 200
        else:
            return 404

class PlateAdd(Resource):
    @swagger.operation()
    def post(self):
        pass

class PlateDelete(Resource):
    @swagger.operation()
    def post(self):
        pass

class PlateUpdate(Resource):
    @swagger.operation()
    def post(self):
        pass

api.add_resource(UserLogin, '/user/login')
api.add_resource(UserLogout, 'user/logout')
api.add_resource(PlateInfo, '/plate/info')
api.add_resource(PlateDelete, '/plate/delete')
api.add_resource(PlateAdd, '/plate/add')
api.add_resource(PlateUpdate, '/plate/update')

def main():
    with app.app_context():
        db.create_all()
    app.run(debug=True)

if __name__ == '__main__':
    main()

