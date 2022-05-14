import faust
from pymongo import MongoClient
from Patient_Mover import patient_upload
from config import connection_string, KAFKA_PROCESSOR_ADDR, KAFKA_PROCESS_TOPIC

mc = MongoClient(connection_string)
HOSPITAL_ZIP_CODES = mc["hospitals"]["hospitals"].distinct("ZIP")

class Schema(faust.Record):
    first_name: str
    last_name: str
    mrn: str
    zip_code: str
    patient_status_code: str

app = faust.App('Faust-Processor', broker=f"kafka://{KAFKA_PROCESSOR_ADDR}")
faust_kafka_topic = app.topic(KAFKA_PROCESS_TOPIC, value_type=Schema)

@app.agent(faust_kafka_topic)
async def process(records: faust.Stream[Schema]) -> None:
    async for r in records:
        new_patient = dict(r.dumps())        
        await patient_upload(new_patient, HOSPITAL_ZIP_CODES)

if __name__ == '__main__':
    app.main()