KAFKA_DIR=/usr/bin/kafka_2.13-2.8.0/;
KAFKA_LOGS_DIR=/tmp/kafka-logs;
ZOOKEEPER_LOGS_DIR=/tmp/zookeeper;

# RUN KILL SCRIPT FIRST!!!
#--------------------------------------------
bash kill_bg.sh >> /dev/null 2>> /dev/null;
# Okay if everything is already dead- nothing gets run into.


#EMPTY OLD KAFKA/ZOOKEEPER AND FAUST LOGS
#--------------------------------------------
#echo "CLEARING LOGS...";
rm -rf $KAFKA_LOGS_DIR/* >> /dev/null 2>> /dev/null;
rm -rf $ZOOKEEPER_LOGS_DIR/* >> /dev/null 2>> /dev/null;

rm -rf background_rtr/*/ >> /dev/null 2>> /dev/null;
rm -rf background_rtr/.* >> /dev/null 2>> /dev/null;

rm -rf logs/* >> /dev/null 2>> /dev/null;

#echo "BG-KILLED"

#RESTART ZOOKEEPER AND KAFKA SERVERS WITH LOGS.
#--------------------------------------------
#echo "RESTARTING ZOOKEEPER, KAFKA SERVERS...";

echo "" > logs/zookeeper-0.log;
bash $KAFKA_DIR/bin/zookeeper-server-start.sh $KAFKA_DIR/config/zookeeper-0.properties >> logs/zookeeper-0.log 2>> logs/zookeeper-0.log &
ZOOKEEPER_0_PID=$!;

echo "" > logs/kafka-transfer.log;
bash $KAFKA_DIR/bin/kafka-server-start.sh $KAFKA_DIR/config/server_transfer.properties >> logs/kafka-transfer.log 2>> logs/kafka-transfer.log &
KAFKA_TRANSFER_PID=$!;

echo "" > logs/zookeeper-1.log;
bash $KAFKA_DIR/bin/zookeeper-server-start.sh $KAFKA_DIR/config/zookeeper-1.properties >> logs/zookeeper-1.log 2>> logs/zookeeper-1.log &
ZOOKEEPER_1_PID=$!;

echo "" > logs/kafka-process.log;
bash $KAFKA_DIR/bin/kafka-server-start.sh $KAFKA_DIR/config/server_process.properties >> logs/kafka-process.log 2>> logs/kafka-process.log &
KAFKA_PROCESS_PID=$!;

# BREAK TIME - Wait for everyone to catch up...
#--------------------------------------------
sleep 5;

# START KAFKA TOPICS
#--------------------------------------------
#echo "CREATING KAFKA TOPICS...";

echo "" > logs/topic-transfer.log;
bash $KAFKA_DIR/bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 50 --topic DataTransfer >> logs/topic-transfer.log 2>> logs/topic-transfer.log

echo "" > logs/topic-process.log;
bash $KAFKA_DIR/bin/kafka-topics.sh --create --bootstrap-server localhost:9093 --replication-factor 1 --partitions 50 --topic DataProcess >> logs/topic-process.log 2>> logs/topic-process.log

# MOVE TO BACKGROUND RTR DIR
#--------------------------------------------
cd background_rtr;

# START FAUST APPS
#--------------------------------------------
#echo "START FAUST APPS...";

echo "" > ../logs/faust-consumer.log;
faust -A Faust_Consumer worker -p 6066 -l info >> ../logs/faust-consumer.log 2>> ../logs/faust-consumer.log &
FAUST_CONSUMER_PID=$!;

echo "" > ../logs/faust-processor.log;
faust -A Faust_Processor worker -p 6067 -l info >> ../logs/faust-processor.log 2>> ../logs/faust-processor.log &
FAUST_PROCESSOR_PID=$!;

# START RMQ TO KAFKA SUBSCRIBER
#--------------------------------------------
#echo "START RMQ SUBSCRIPTION"

echo "" > ../logs/Subscriber.log;
python -u Server_Subscriber.py >> ../logs/Subscriber.log 2>> ../logs/Subscriber.log &
SUBSCRIBER_PID=$!;

# MOVE BACK TO MAIN DIR
#--------------------------------------------
cd ..;

# SAVE ALL RUNNING PROCESSES TO LOG
#--------------------------------------------
echo "$ZOOKEPER_0_PID $KAFKA_TRANSFER_PID $ZOOKEEPER_1_PID $KAFKA_PROCESS_PID $FAUST_CONSUMER_PID $FAUST_PROCESSOR_PID $SUBSCRIBER_PID" > logs/Running_Processes.pids;

# BREAK TIME - Wait for everyone to catch up...
#--------------------------------------------
sleep 5;
#echo "APPLICATION-RESET";