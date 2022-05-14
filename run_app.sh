bash kill_app.sh;

echo "STARTING-UP";

bash reset.sh;

echo "" > flask-logs/flask.out; echo "" > flask-logs/flask.pid;

python app.py START_SERVER >> flask-logs/flask.out 2>> flask-logs/flask.out &

FLASK_PID=$!;
echo "$FLASK_PID" >> flask-logs/flask.pid;

echo "APP-IS-LIVE";