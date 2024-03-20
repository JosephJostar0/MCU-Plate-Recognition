import requests

CHECK_PLATE = 'http://localhost:5000/plate/check'
SET_PLATE = 'http://localhost:5000/plate/set'

class ToBackend:
    @staticmethod
    def checkPlate(plate:str) -> str:
        data = {
            'number' : plate
        }
        try:
            res = requests.post(CHECK_PLATE, data=data, timeout=1)
            return res.json().get('status')
        except:
            return "unrecorded plate." 
    
    @staticmethod
    def setPlate(plate:str):
        data = {
            'number':plate,
        }
        try:
            requests.post(SET_PLATE, data=data, timeout=1)
        except:
            return
