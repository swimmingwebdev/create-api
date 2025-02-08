import connexion
from connexion import NoContent
from models import Base, TrackAlerts, TrackLocations
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import yaml
import logging.config

# Configurations
with open('../storage/config/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Logging
with open('../storage/config/log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# mysql
# Load database config
db_user = app_config["datastore"]["user"]
db_password = app_config["datastore"]["password"]
db_hostname = app_config["datastore"]["hostname"]
db_port = app_config["datastore"]["port"]
db_name = app_config["datastore"]["db"]

# Initialize the engine
db_url = f"mysql+mysqldb://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"
engine = create_engine(db_url)

def make_session():
    return sessionmaker(bind=engine)()

# Store event 1 data
def trackGPS(body):
    session = make_session()

    timestamp = datetime.fromisoformat(body["timestamp"].replace("Z", "+00:00"))
    trace_id = body["trace_id"]

    event = TrackLocations(
            device_id=body["device_id"],
            latitude=body["latitude"],
            longitude=body["longitude"],
            location_name=body["location_name"],
            timestamp=timestamp,
            trace_id=trace_id
    )
    session.add(event)
    session.commit()
    session.close()

    # Logging when event is successfully stored
    logger.debug(f"Stored event trackGPS with a trace id of {trace_id}")

    return NoContent, 201

# Store event 2 data
def trackAlerts(body):
    session = make_session()

    timestamp = datetime.fromisoformat(body["timestamp"].replace("Z", "+00:00"))
    trace_id = body["trace_id"]

    event = TrackAlerts(
        device_id=body["device_id"], # body.get("device_id") : returns None
        latitude=body["latitude"],
        longitude=body["longitude"],
        location_name=body["location_name"],
        alert_desc=body["alert_desc"],
        timestamp=timestamp,
        trace_id=trace_id 
    )
    session.add(event)
    session.commit()
    session.close()

    # Use DEBUG level for stored events as specified
    logger.debug(f"Stored event trackAlerts with a trace id of {trace_id}")

    return NoContent, 201


# Get Location events
def get_trackGPS(start_timestamp, end_timestamp):
    session = make_session()

    start =  datetime.fromisoformat(start_timestamp.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_timestamp.replace("Z", "+00:00"))

    statement = select(TrackLocations).where(
        TrackLocations.timestamp >= start, 
        TrackLocations.timestamp < end
        )
    results = [
        result.to_dict() 
        for result in session.execute(statement).scalars().all()
    ]

    session.close()

    logger.info("Found %d trackGPSs (start: %s, end: %s)", 
                len(results), 
                start.strftime("%Y-%m-%dT%H:%M:%S"), 
                end.strftime("%Y-%m-%dT%H:%M:%S"))

    return results


# Get Alert events
def get_trackAlerts(start_timestamp, end_timestamp):
    session = make_session()

    start = datetime.fromisoformat(start_timestamp.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_timestamp.replace("Z", "+00:00"))

    statement = select(TrackAlerts).where(
        TrackAlerts.timestamp >= start, 
        TrackAlerts.timestamp < end
        )
    results = [
        result.to_dict() 
        for result in session.execute(statement).scalars().all()
    ]

    session.close()

    logger.info("Found %d trackAlerts (start: %s, end: %s)", 
                len(results), 
                start.strftime("%Y-%m-%dT%H:%M:%S"),
                end.strftime("%Y-%m-%dT%H:%M:%S"))

    return results


app = connexion.FlaskApp(__name__, specification_dir='.')
app.add_api("../storage/config/openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    logger.info("Receiver Service received")
    app.run(port=8090)