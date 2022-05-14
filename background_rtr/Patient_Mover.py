import pymongo
from pymongo import MongoClient
from config import connection_string

#This is the function that controls how data is updated in mongodb
async def patient_upload(patient_record, HOSPITAL_ZIP_CODES):
    
    client = MongoClient(connection_string)
    patients = client["patients"]["patients"]
    hospitals = client['hospitals']['hospitals']
    zips = client['zip-codes']['zip-distances'] 

    SYMPTOMATIC_CODES = "356"
    HOME_ASSIGNMENT = 1

    assigned_loc = HOME_ASSIGNMENT
    status_code = patient_record["patient_status_code"]

    if status_code in (SYMPTOMATIC_CODES):

        if status_code in "35":

            hospital_dists = zips \
                .find({"zip_from": int(patient_record["zip_code"]), "zip_to": {"$in": HOSPITAL_ZIP_CODES}})

            if hospital_dists:
                hospital_dists = hospital_dists.sort([('distance', pymongo.ASCENDING)])

            for h_dist in hospital_dists:

                hospitals_in_zip = hospitals.find({"ZIP": h_dist["zip_to"]})

                break_flag = False
                for h in hospitals_in_zip:
                    if (h["AVAILABLE_BEDS"] > 0):
                        hospitals.update_one({"ID": h["ID"]}, {'$inc': {'AVAILABLE_BEDS': -1}})
                        assigned_loc = h["ID"]
                        break_flag = True
                        break

                if break_flag:
                    break

        else: # status_code 6, critical nature

            ordinals_levels = ["LEVEL IV", "LEVEL III", "LEVEL II", "LEVEL I", "NOT AVAILABLE"]

            for o in ordinals_levels:
                
                if hospitals.count_documents({"AVAILABLE_BEDS": {"$gt": 0}, "TRAUMA": o}) > 0:
                    
                    valid_hospitals = hospitals.find({"AVAILABLE_BEDS": {"$gt": 0}, "TRAUMA": o})
                    valid_zips = valid_hospitals.distinct("ZIP")
            
                    hospital_dists = zips.find({"zip_from": int(patient_record["zip_code"]), "zip_to": {"$in": valid_zips}})
                    hospital_dists = hospital_dists.sort([('distance', pymongo.ASCENDING)])
                    chosen_zip = hospital_dists[0]["zip_to"]

                    valid_hospitals = hospitals.find({"AVAILABLE_BEDS": {"$gt": 0}, "TRAUMA": o, "ZIP": chosen_zip})
                    chosen_hospital = valid_hospitals.sort([("AVAILABLE_BEDS", pymongo.DESCENDING)])[0]["ID"]
                    hospitals.update_one({"ID": chosen_hospital}, {"$inc": {"AVAILABLE_BEDS": -1}})
                    assigned_loc = chosen_hospital
                    break

    patients.update_one({"mrn": patient_record["mrn"]}, {"$set": {"location_code": assigned_loc}})