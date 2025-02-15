import connexion
from connexion import NoContent
from models import Base, TrackAlerts, TrackLocations
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import yaml
import logging.config
import json
import time
from pykafka import KafkaClient
from threading import Thread
from pykafka.common import OffsetType

# Configurations
with open('config/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Logging
with open('config/log_conf.yml', 'r') as f:
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
# Load Kafka config
KAFKA_HOSTNAME = app_config["events"]["hostname"] 
KAFKA_PORT = app_config["events"]["port"] 
KAFKA_TOPIC = app_config["events"]["topic"] 

# Initialize the engine
db_url = f"mysql+mysqldb://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"
engine = create_engine(db_url)
# Create missing tables
Base.metadata.create_all(engine)

def make_session():
    return sessionmaker(bind=engine)()

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

    logger.info(f"Found {len(results)} trackGPS events (start: {start}, end: {end})")

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

    logger.info(f"Found {len(results)} trackAlerts events (start: {start}, end: {end})")

    return results

def process_messages():
    """ Process event messages """
    while True:  # Keep the consumer running even if it crashes
        try:
            hostname = f"{KAFKA_HOSTNAME}:{KAFKA_PORT}"
            client = KafkaClient(hosts=hostname)
            topic = client.topics[KAFKA_TOPIC.encode("utf-8")]

            consumer = topic.get_simple_consumer(
                consumer_group=b"event_group",
                reset_offset_on_start=False,
                auto_offset_reset=OffsetType.LATEST
            )

            logger.info("Kafka Consumer started, waiting for messages")
            
            # Stay in the loop, waiting for new messages
            for msg in consumer:
                try:
                    msg_str = msg.value.decode("utf-8")
                    msg = json.loads(msg_str)

                    logger.info("Message: %s" % msg)

                    payload = msg["payload"]

                    session = make_session()
                    timestamp = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
                    trace_id = payload["trace_id"]        

                    if msg["type"] == "TrackGPS":
                        event = TrackLocations(
                            device_id=payload["device_id"],
                            latitude=payload["latitude"],
                            longitude=payload["longitude"],
                            location_name=payload["location_name"],
                            timestamp=timestamp,
                            trace_id=trace_id
                        )
                        session.add(event)
                        session.commit()

                        # Logging when event is successfully stored
                        logger.debug(f"Stored trackGPS event with trace id {trace_id}")

                    elif msg["type"] == "TrackAlerts":
                        # Store the event2 to the DB 
                        event = TrackAlerts(
                            device_id=payload["device_id"],
                            latitude=payload["latitude"],
                            longitude=payload["longitude"],
                            location_name=payload["location_name"],
                            alert_desc=payload["alert_desc"],
                            timestamp=timestamp,
                            trace_id=trace_id 
                        )
                        session.add(event)
                        session.commit()
                        
                        # Use DEBUG level for stored events as specified
                        logger.debug(f"Stored event trackAlerts with a trace id of {trace_id}")
                    
                finally:
                    session.close()  # Ensure session closes every time
                
                consumer.commit_offsets()
        
        except Exception as e:
            logger.error(f"Kafka Consumer crashed: {e}")
            time.sleep(5) # Wait before restarting
        

# thread to consume messages
def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

app = connexion.FlaskApp(__name__, specification_dir='.')
app.add_api("config/openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    logger.info("Receiver Service received")
    setup_kafka_thread()
    app.run(port=8090)