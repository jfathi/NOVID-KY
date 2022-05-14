#!/usr/bin/env python
from json import loads, dumps
from kafka.producer.kafka import KafkaProducer
import pika
import sys

from config import KAFKA_COUNTER_ADDR, KAFKA_COUNT_TOPIC, \
    KAFKA_HOST_COUNTER, KAFKA_PORT_COUNTER

kp = KafkaProducer(
    bootstrap_servers=f"{KAFKA_COUNTER_ADDR}",
)

def callback(ch, method, properties, body: bytes):
    new_body = loads(body)
    for r in new_body:
        kp.send(KAFKA_COUNT_TOPIC, bytes(dumps(r), "utf-8"))
    print(f'Successful transmission to {KAFKA_COUNTER_ADDR} ({KAFKA_COUNT_TOPIC})')

# Set the connection parameters to connect to rabbit-server1 on port 5672
# on the / virtual host using the username "guest" and password "guest"
def Subscribed_Consumer(host=KAFKA_HOST_COUNTER, port=KAFKA_PORT_COUNTER):

    username = 'student'
    password = 'student01'
    hostname = 'localhost'
    virtualhost = '7'
    
    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(hostname,
                                            5672,
                                            virtualhost,
                                            credentials,
                                            blocked_connection_timeout=0)
    
    connection = pika.BlockingConnection(parameters)
    
    channel = connection.channel()
    
    exchange_name = 'patient_data'
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')
    
    result = channel.queue_declare('', exclusive=True)
    queue_name = result.method.queue
    
    binding_keys = "#"
    
    if not binding_keys:
        sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
        sys.exit(1)
    
    for binding_key in binding_keys:
        channel.queue_bind(
            exchange=exchange_name, queue=queue_name, routing_key=binding_key)
    
    print(' [*] Waiting for logs. To exit press CTRL+C')
    
    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=True)
    
    channel.start_consuming()
    
Subscribed_Consumer()