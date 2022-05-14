import pymongo
import subprocess
from flask import Blueprint
from .config import connection_string

reset = Blueprint("reset", __name__)
@reset.route("/api/reset", methods=["GET"])
def app_reset():

    RESET_FAILURE = "0"
    RESET_SUCCESS = "1"
    reset_status_code = RESET_FAILURE
    
    BASH_SUCCESS = 0
    RESET_BASH = "reset.sh"
    KILL_BG_BASH = "kill_bg.sh"

    try:

        # Run kill script. (We'll need to fix the java pkill!) 
        # Await the echo response "BG-KILLED"
        cmd_line = f"bash {KILL_BG_BASH}".split()
        response = subprocess.call(cmd_line)
        assert(response == BASH_SUCCESS)

        client = pymongo.MongoClient(connection_string)

        app_patients = client["patients"]["patients"]
        app_hospitals = client["hospitals"]["hospitals"]
        hospital_defaults = client["hospitals"]["hospitals-default"]

        n_patients = app_patients.count_documents({})
        n_hospitals = app_hospitals.count_documents({})
        n_default_hospitals = hospital_defaults.count_documents({})

        patients_deleteResult = app_patients.delete_many({})
        hospitals_deleteResult = app_hospitals.delete_many({})

        assert(patients_deleteResult.deleted_count == n_patients)
        assert(hospitals_deleteResult.deleted_count == n_hospitals)

        hospitals_insertResult = app_hospitals.insert_many(hospital_defaults.find({}))

        assert(len(hospitals_insertResult.inserted_ids) == n_default_hospitals)

        app_hospitals.aggregate([
            {"$addFields": {"AVAILABLE_BEDS": "$BEDS"}}, 
            {"$out": "hospitals"}
            ])

        assert(app_hospitals.count_documents({"AVAILABLE_BEDS": {"$exists": False}}) == 0)

        # Run reset script. Await the echo response. "APPLICATION-RESET"
        cmd_line = f"bash {RESET_BASH}".split()
        response = subprocess.call(cmd_line)
        assert(response == BASH_SUCCESS)

        reset_status_code = RESET_SUCCESS

    except Exception as e:
        print(e)
    
    return {"reset_status_code": reset_status_code}