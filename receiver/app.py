import connexion
from connexion import NoContent
from datetime import datetime
import httpx
import yaml 
import logging.config
import time

# Configurations
with open('../receiver/config/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Logging
with open('../receiver/config/log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# URL from config
EVENT1_URL = app_config["eventstore1"]["url"]
EVENT2_URL = app_config["eventstore2"]["url"] 

logger = logging.getLogger('basicLogger')

# Event 1
def trackGPS(body):

    trace_id = time.time_ns()

    # Logging when an event is received
    logger.info(f"Received event trackGPS with a trace id of {trace_id}")


    received_timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    
    data = {
            "device_id": body["device_id"],
            "latitude": body["latitude"],
            "longitude": body["longitude"],
            "location_name": body.get("location_name", "unknown"),
            "timestamp": received_timestamp,
            "trace_id" : trace_id,
    }

    # Send data to database
    response = httpx.post(EVENT1_URL, json=data)
    
    # Logging the reseponse of storage service
    logger.info(f"Response for event trackGPS (id: {trace_id}) has status {response.status_code}")

    return NoContent, 201


# Event 2
def trackAlerts(body):
    trace_id = time.time_ns()

    # Logging when an event is received
    logger.info(f"Received event trackAlerts with a trace id of {trace_id}")

    
    received_timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    
    data = {
            "device_id": body["device_id"],
            "latitude": body["latitude"],
            "longitude": body["longitude"],
            "location_name": body.get("location_name", "unknown"),
            "alert_desc": body.get("alert_desc", "No description provided."),
            "timestamp": received_timestamp,
            "trace_id" : trace_id,

    }

    # Send data to database
    response = httpx.post(EVENT2_URL, json=data)

    # Logging the reseponse of storage service 
    logger.info(f"Response for event trackAlerts (id: {trace_id}) has status {response.status_code}")

    return NoContent, 201



app = connexion.FlaskApp(__name__, specification_dir='.')
app.add_api("../receiver/config/openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    logger.info("Receiver Service received")
    app.run(port=8080)