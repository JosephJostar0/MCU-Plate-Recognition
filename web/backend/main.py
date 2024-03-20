from pydantic import BaseModel
from flask_openapi3 import Info, Tag
from flask_openapi3 import OpenAPI
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from flask import session
from queue import Queue

info = Info(title="License Plate API", version="1.0.0")
app = OpenAPI(__name__, info=info)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.sqlite3'
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'your_secret_key_here'
db:SQLAlchemy = SQLAlchemy(app)
CORS(app)

plateQueue = Queue()

# const
class UserService:
    @staticmethod
    def getAdmin():
        ADMIN = 'admin'
        PASSWORD = '123456aaa'
        return ADMIN, PASSWORD
        
    @staticmethod
    def isAdmin(uname:str, pwd:str) -> bool:
        return (uname, pwd) == UserService.getAdmin()

class PlateService:
    @staticmethod
    def isPlateValid(plate:str):
        return len(plate) < 16
    
PLATE_TAG = [Tag(name="plate", description="license plate management")]
USER_TAG = [Tag(name="user", description="login & logout")]

class MyResponse:
    @staticmethod
    def success(data:list=[]):
        return {
            "code":0,
            "status": "ok",
            "data" : data,
            "total" : len(data),
        }
    
    @staticmethod
    def fail(msg:str=""):
        return {
            "code":1,
            "status": msg if len(msg)>0 else "fail",
            "data":[],
            "total": 0,
        }, 201

# db Models
class Plate(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(16), unique=True, nullable=False)
    access = db.Column(db.Integer, default=0)
    period = db.Column(db.Integer, default=int(datetime.now().timestamp()))

    def toJson(self) -> dict:
        return {
            'pid': self.pid,
            'number': self.number,
            'access': self.access,
            # 'period': self.period,
        }

    def __repr__(self) -> str:
        return str(self.toJson()) 


# request models
class PlateAddRequest(BaseModel):
    number:str
    # access:int
    # period:int

class PlateDeleteRequest(BaseModel):
    pid:int

class PlateUpdateRequest(BaseModel):
    pid:int
    number:str
    access:int
    # period:int

class PlateCheckRequest(BaseModel):
    number:str

class LoginRequest(BaseModel):
    uname:str
    password:str


# backend api
@app.post("/user/login", summary="login", tags=USER_TAG)
def userLogin(body:LoginRequest):
    if UserService.isAdmin(body.uname, body.password):
        session['uname'] = body.uname
        return MyResponse.success()
    else:
        return MyResponse.fail("Invalid username or password.")

@app.post("/user/logout", summary="logout", tags=USER_TAG)
def userLogout():
    # if 'uname' in session:
    #     session.pop('uname')
    #     return MyResponse.success()
    # else:
    #     return MyResponse.fail("No active session.")
    return MyResponse.success()

@app.post("/plate/add", summary="add plate", tags=PLATE_TAG)
def addPlate(body:PlateAddRequest):
    # if 'uname' not in session or session['uname'] != 'admin':
        # return MyResponse.fail("No active session.")
    if Plate.query.filter_by(number=body.number).first() is not None:
        return MyResponse.fail("License Plate has been recorded, do not re-enter.")
    if not PlateService.isPlateValid(body.number):
        return MyResponse.fail("Invalid license plate.")
    plate = Plate(number=body.number)
    db.session.add(plate)
    db.session.commit()
    return MyResponse.success()

@app.post("/plate/delete", summary="delete plate", tags=PLATE_TAG)
def deletePlate(body:PlateDeleteRequest):
    # if 'uname' not in session or session['uname'] != 'admin':
        # return MyResponse.fail("No active session.")
    plate = Plate.query.filter_by(pid=body.pid).first()
    if plate is None:
        return MyResponse.fail("pid is out of range.")
    db.session.expunge(plate)
    db.session.delete(plate)
    db.session.commit()
    return MyResponse.success()

@app.post("/plate/update", summary="update plate", tags=PLATE_TAG)
def updatePlate(body:PlateUpdateRequest):
    # if 'uname' not in session or session['uname'] != 'admin':
        # return MyResponse.fail("No active session.")
    plate:Plate = Plate.query.filter_by(pid=body.pid).first()
    if plate is None:
        return MyResponse.fail("pid is out of range.")
    if body.number != plate.number:
        if not Plate.query.filter_by(number=body.number).first() is None:
            return MyResponse.fail("License Plate has been recorded, do not re-enter.")
    plate.access = body.access
    if not PlateService.isPlateValid(body.number):
        return MyResponse.fail("Invalid license number.")
    plate.number = body.number
    # plate.period = body.period
    db.session.commit()
    return MyResponse.success()

@app.post("/plate/list", summary="list plate", tags=PLATE_TAG)
def listPlate():
    # if 'uname' not in session or session['uname'] != 'admin':
        # return MyResponse.fail("No active session.")
    plates = Plate.query.all()
    return MyResponse.success([it.toJson() for it in plates])
    
@app.post("/plate/alter", summary="alter access", tags=PLATE_TAG)
def alterPlate(body:PlateDeleteRequest):
    plate:Plate = Plate.query.filter_by(pid=body.pid).first()
    if plate is None:
        return MyResponse.fail("pid is out of range.")
    plate.access = (plate.access + 1) % 2
    db.session.commit()
    return MyResponse.success()


@app.post("/plate/check", summary="check plate", tags=PLATE_TAG)
def checkPlate(body:PlateCheckRequest):
    plate:Plate = Plate.query.filter_by(number=body.number).first() 
    if plate is None:
        return MyResponse.fail("Invalid License Plate.")
    # current = datetime.now().timestamp()
    # if not plate.access or current > plate.period:
    #     return MyResponse.fail("This car has no access.")
    return MyResponse.success('valid access.')

@app.post("/plate/current", summary="get current plate", tags=PLATE_TAG)
def currentPlate():
    flag = 0
    number = "no plate detected."
    try:
        number = plateQueue.get(timeout=0.1)
        plate:Plate = Plate.query.filter_by(number=number).first()
        if not plate is None:
            flag = plate.access
    except TimeoutError:
        pass
    finally:
        return MyResponse.success([{
            "plate":number,
            "access": flag,
        }])

@app.post("/plate/set", summary="set current plate", tags=PLATE_TAG)
def setPlate(body:PlateCheckRequest):
    number = body.number
    plateQueue.put(number)
    return MyResponse.success()

def main():
    with app.app_context():
        db.create_all()
    app.run(debug=True)

if __name__ == "__main__":
    main()
