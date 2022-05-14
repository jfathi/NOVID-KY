import faust
from json import dumps
from kafka import KafkaProducer
from pymongo import MongoClient
from config import connection_string,\
    KAFKA_COUNTER_ADDR, KAFKA_PROCESSOR_ADDR,\
    KAFKA_COUNT_TOPIC, KAFKA_PROCESS_TOPIC

POSITIVE_STATUS_CODES = [3,5,6]
HOME_ASSIGNMENT_STATUSES = [0,1,2,4]
POSITIVE_STATUS_CODES = ''.join([str(d) for d in POSITIVE_STATUS_CODES])
HOME_ASSIGNMENT_STATUSES = ''.join([str(d) for d in HOME_ASSIGNMENT_STATUSES])

mc = MongoClient(connection_string)
patients = mc["patients"]["patients"]

kp = KafkaProducer(
    bootstrap_servers=f"{KAFKA_PROCESSOR_ADDR}",
)

VALID_ZIP_CODES = mc["zip-codes"]["zip-distances"].distinct("zip_from") 
HOSPITAL_ZIP_CODES = mc["hospitals"]["hospitals"].distinct("ZIP")

STATUS_FILENAME = "zip.status"
STATUS_LOGS = open(STATUS_FILENAME, "w+"); STATUS_LOGS.close()

WINDOW_TIME = 15.0 # in seconds

NO_ALERT = 0
ON_ALERT = 1
STATE_ALERT_MIN = 5

class Schema(faust.Record):
    first_name: str
    last_name: str
    mrn: str
    zip_code: str
    patient_status_code: str

n_negative_tests = 0
n_positive_tests = 0

app = faust.App('Faust-Consumer', broker=f"kafka://{KAFKA_COUNTER_ADDR}")
faust_kafka_topic = app.topic(KAFKA_COUNT_TOPIC, value_type=Schema)

ky_covid_cases = app.Table('cases-by-county', default=int)
windowed_covid_cases = ky_covid_cases.tumbling(
    2*WINDOW_TIME,
    expires= 60,
    key_index=True
)

@app.timer(0.3)
async def evaluation() -> None:
    
    zip_list = []
    for r in windowed_covid_cases:
        zip_cases_overall = len(
            windowed_covid_cases
                .relative_to_now().values()
        )
        if zip_cases_overall == 0:
            continue
        zip_cases_new = len(
            windowed_covid_cases
            .relative_to_now()[zip]
            .items().delta(WINDOW_TIME)
        )
        zip_cases_prev = zip_cases_overall - zip_cases_new
        if zip_cases_new >= 2 * zip_cases_prev:
            zip_list.append(r.zip_code)
    
    zip_list.sort()

    if len(zip_list) >= STATE_ALERT_MIN:
        state_status = ON_ALERT
    else:
        state_status = NO_ALERT

    STATUS_LOGS = open(STATUS_FILENAME, "a")
    STATUS_LOGS.write(str({
        "ziplist": zip_list,
        "state_status": state_status,
        "positive_test": n_positive_tests,
        "negative_test": n_negative_tests
    }) + '\n')
    STATUS_LOGS.close()

@app.agent(faust_kafka_topic)
async def process(records: faust.Stream[Schema]) -> None:
    global n_positive_tests, n_negative_tests, ky_covid_cases
    async for r in records:
        zip = r.zip_code
        
        last_pos_count = ky_covid_cases.get(zip) 
        new_pos_count = last_pos_count if last_pos_count != None else 0
        
        if r.patient_status_code in POSITIVE_STATUS_CODES:
            new_pos_count += 1
            n_positive_tests += 1
        else:
            n_negative_tests += 1

        for k,_ in ky_covid_cases.items():
            if k == zip:
                ky_covid_cases.update(k,new_pos_count)

        new_patient = dict(r.dumps())
        if r.patient_status_code in HOME_ASSIGNMENT_STATUSES:
            new_patient.update({"location_code": 0})
        else:
            new_patient.update({"location_code": -1})
        new_patient.pop("__faust")

        patients.insert_one(new_patient)

        r_json = {
            "first_name": r.first_name,
            "last_name": r.last_name,
            "mrn": r.mrn,
            "zip_code": r.zip_code,
            "patient_status_code": r.patient_status_code
        }
        if new_patient["location_code"] == -1:
            kp.send(KAFKA_PROCESS_TOPIC, bytes(dumps(r_json), "utf-8"))

if __name__ == '__main__':
    app.main()