import connexion
from connexion import NoContent

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from blood_pressure import BloodPressure
from heart_rate import HeartRate
import datetime

DB_ENGINE = create_engine("sqlite:///readings.sqlite")
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def report_blood_pressure_reading(body):
    """ Receives a blood pressure reading """

    session = DB_SESSION()

    bp = BloodPressure(body['patient_id'],
                       body['device_id'],
                       body['timestamp'],
                       body['blood_pressure']['systolic'],
                       body['blood_pressure']['diastolic'])

    session.add(bp)

    session.commit()
    session.close()

    return NoContent, 201


def report_heart_rate_reading(body):
    """ Receives a heart rate (pulse) reading """

    session = DB_SESSION()

    hr = HeartRate(body['patient_id'],
                   body['device_id'],
                   body['timestamp'],
                   body['heart_rate'])

    session.add(hr)

    session.commit()
    session.close()

    return NoContent, 201

    return NoContent, 200


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8090)
