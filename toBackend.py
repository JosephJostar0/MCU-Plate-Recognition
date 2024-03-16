import requests

CHECK_PLATE = 'http://localhost:5000/plate/check'

class ToBackend:
    @staticmethod
    def checkPlate(plate:str):
        data = {
            'number' : plate
        }
        res = requests.post(CHECK_PLATE, data=data)
        return res.status_code == 200
