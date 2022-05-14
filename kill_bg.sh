KAFKA_LOGS_DIR=/tmp/kafka-logs;
ZOOKEEPER_LOGS_DIR=/tmp/zookeeper;

#KILL ALL PREVIOUS (NON-APP) PROCESSES - SERVERS, FAUST, THE WORKS
#--------------------------------------------
#echo "KILLING PROCESSES...";

touch logs/Running_Processes.pids;
kill -9 $(<logs/Running_Processes.pids) >> /dev/null 2>> /dev/null;
pkill -9 java; # For now... But we should eliminate this.

fuser -k 9092/tcp >> /dev/null 2>> /dev/null;
fuser -k 9093/tcp >> /dev/null 2>> /dev/null;
fuser -k 6066/tcp >> /dev/null 2>> /dev/null;
fuser -k 6067/tcp >> /dev/null 2>> /dev/null;
fuser -k 2181/tcp >> /dev/null 2>> /dev/null;
fuser -k 2182/tcp >> /dev/null 2>> /dev/null;