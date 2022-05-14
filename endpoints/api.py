from json import loads
from flask import Blueprint
from pymongo import MongoClient
from os import SEEK_END, SEEK_CUR
from .config import connection_string

api = Blueprint("api", __name__)

SYS_STATUS_FILE = 'background_rtr/zip.status'

def get_background_state():
    last_line = ""
    with open(SYS_STATUS_FILE, 'rb') as f:
        f.seek(-2, SEEK_END)
        while f.read(1) != b"\n":
            f.seek(-2, SEEK_CUR)
        last_line = f.readline().decode("utf-8")
        last_line = last_line.replace("'", '"')
    return loads(last_line)

#Returns the app_status_code and the team ID names
@api.route('/api/getteam', methods = ["GET"])
def get_team():
    return {"team_name": "Team X",
	"app_status_code": "1"
    }


@api.route('/api/getpatient/<string:mrn>', methods = ["GET"])
def get_patient_location(mrn):

    client = MongoClient(connection_string)
    db = client['patients']
    patients = db['patients']
    
    patInfo = patients.find_one({"mrn": mrn})
    if patInfo:
        location = patInfo['location_code']
    else:
        location = "NOT-IN-SYSTEM"

    return {"mrn": mrn, "location_code": location}


# using hospital ID reports the total number of beds
# reports the avalable_beds
# gives the zipcode of the hospital
@api.route('/api/gethospital/<int:id>', methods = ["GET"] )
def get_hospital(id):
    
    client = MongoClient(connection_string)
    db = client['hospitals']
    hospitals = db['hospitals']

    hostInfo = hospitals.find_one({"ID" : id})

    if hostInfo:
        avaBeds = hostInfo['AVAILABLE_BEDS']
        totBeds = hostInfo['BEDS']
        zipCode = hostInfo['ZIP']
    else:
        avaBeds, totBeds = 0, 0
        zipCode = -1

    return {"total_beds": totBeds, "available_beds": avaBeds, "zipcode": zipCode}

@api.route('/api/zipalertlist')
def get_zip_alerts():
    app_status: dict = get_background_state()
    ziplist = app_status.get("ziplist")
    return {"ziplist": ziplist}

@api.route('/api/alertlist')
def get_state_alert():
    app_status: dict = get_background_state()
    state_status = app_status.get("state_status")
    return {"state_status": state_status}

@api.route('/api/testcount')
def get_state_counts():
    app_status: dict = get_background_state()
    postive_count = app_status.get("positive_test")
    negative_count = app_status.get("negative_test")
    return {"positve_test": postive_count, "negative_test": negative_count}