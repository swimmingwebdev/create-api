import connexion
from connexion import NoContent
from datetime import datetime, timezone
import yaml 
import logging.config
import json
from apscheduler.schedulers.background import BackgroundScheduler
import os
import httpx
import asyncio
from asgiref.sync import async_to_sync


# Configurations
with open("/config/app_conf.yml", "r") as f:
    app_config = yaml.safe_load(f.read())

# Make sure the logs directory exists
log_directory = "/app/logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Logging
with open('/config/log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('processingLogger')

# URL from config
GPS_URL = app_config["eventstores"]["track_locations"]["url"]
ALERTS_URL = app_config["eventstores"]["track_alerts"]["url"]

STATS_FILE = "/app/data/stats.json"

# if os.path.exists(STATS_FILE):
#     with open(STATS_FILE, "r") as f:
#         stats = json.load(f)

#     stats["last_updated"] = "2000-01-01T00:00:00+00:00"

#     with open(STATS_FILE, "w") as f:
#         json.dump(stats, f, indent=2)

#     print("Reset 'last_updated' to 2000-01-01T00:00:00+00:00")
# else:
#     print("stats.json not found!")

# Initialize default stats
def initialize_stats():
    try:
        if not os.path.exists(STATS_FILE):
            # default local time timestamp
            # to set based on the local system timezone
            default_time = datetime(2000, 1, 1).astimezone().isoformat()
            stats = {
                "num_gps_events": 0,
                "num_alert_events": 0,
                "max_alerts_per_day": 0,
                "peak_gps_activity_day": 0,
                "last_updated": default_time
            }

            with open(STATS_FILE, "w") as f:
                json.dump(stats, f, indent=2) 
                logger.info(f"Created new stats file at {STATS_FILE}")    
            return stats
        else:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error in initialize_stats: {str(e)}")
        default_time = datetime(2000, 1, 1).astimezone().isoformat()
        return {
            "num_gps_events": 0,
            "num_alert_events": 0,
            "max_alerts_per_day": 0,
            "peak_gps_activity_day": 0,
            "last_updated": default_time
        }


async def populate_stats():
    logger.info("Periodic processing has started")

    try:
        stats = initialize_stats()

        last_str = stats['last_updated']  

        end_str = datetime.now().astimezone().isoformat()

        last_updated = last_str.replace("+", "%2B")
        current_time = end_str.replace("+", "%2B")
        
        # httpx
        async with httpx.AsyncClient() as client:
            gps_response = await client.get(
                f"{GPS_URL}?start_timestamp={last_updated}&end_timestamp={current_time}"
            )
            alerts_response = await client.get(
                f"{ALERTS_URL}?start_timestamp={last_updated}&end_timestamp={current_time}"
            )

        # gps_response = requests.get(
        #     f"{GPS_URL}?start_timestamp={last_updated}&end_timestamp={current_time}"
        #     )
        # alerts_response = requests.get(
        #     f"{ALERTS_URL}?start_timestamp={last_updated}&end_timestamp={current_time}"
        #     )

        # Check response codes
        if gps_response.status_code != 200 or alerts_response.status_code != 200:
            logger.error(
                f"GPS status: {gps_response.status_code}, "
                f"Alerts status: {alerts_response.status_code}"
            )
            return
        
        gps_events = gps_response.json()
        alerts_events = alerts_response.json()
        
        logger.info(
            f"Received events - GPS: {len(gps_events)}, Alerts: {len(alerts_events)}"
        )

        # cumulative number for events
        stats["num_gps_events"] += len(gps_events)
        stats["num_alert_events"] += len(alerts_events)
        
        # Calculate max alerts
        if alerts_events:
            daily_alerts = {}
            for event in alerts_events:
                date = event["timestamp"].split("T")[0]
                daily_alerts[date] = daily_alerts.get(date, 0) + 1

            current_max_alerts = max(daily_alerts.values(), default=0)
            stats["max_alerts_per_day"] = max(stats["max_alerts_per_day"], current_max_alerts)
  
        # Calculate peak GPS
        if gps_events:
            daily_gps = {}
            for event in gps_events:
                date = event["timestamp"].split("T")[0]
                daily_gps[date] = daily_gps.get(date, 0) + 1

            current_peak_gps = max(daily_gps.values(), default=0)
            stats["peak_gps_activity_day"] = max(stats["peak_gps_activity_day"], current_peak_gps)
        
        stats["last_updated"] = current_time

        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)
        
        logger.debug(f"Updated statistics: {stats}")
        logger.info("Periodic processing has ended")

    except Exception as e:
        logger.error(f"Error in populate_stats: {str(e)}")    

async def get_stats():

    logger.info("Stats request received.")

    if not os.path.exists(STATS_FILE):
        logger.error("Statistics file does not exist.")
        return {"message": "Statistics do not exist."}, 404

    with open(STATS_FILE, "r") as f:
        stats = json.load(f)

    logger.debug(f"Stats contents: {stats}")

    logger.info("Stats request completed.")

    return stats, 200

# to setup a periodic call to the function
def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(lambda: async_to_sync(populate_stats)(), "interval", seconds=app_config["scheduler"]["interval"])
    # sched.add_job(lambda: asyncio.run(populate_stats()), "interval", seconds=app_config["scheduler"]["interval"])
    # sched.add_job(populate_stats, 
    #               "interval", 
    #               seconds=app_config["scheduler"]["interval"])
    sched.start()
    logger.info("Scheduler started")

app = connexion.FlaskApp(__name__, specification_dir=".")
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    logger.info("Processing Service started")
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")