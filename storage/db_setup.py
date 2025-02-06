from models import Base
from sqlalchemy import create_engine
import yaml

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

db_user = app_config["datastore"]["user"]
db_password = app_config["datastore"]["password"]
db_hostname = app_config["datastore"]["hostname"]
db_port = app_config["datastore"]["port"]
db_name = app_config["datastore"]["db"]

db_url = f"mysql+mysqldb://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"

engine = create_engine(db_url)

def create_tables():
    Base.metadata.create_all(engine)

    print("Tables created successfully.")

def drop_tables():
    Base.metadata.drop_all(engine)

    print("Tables dropped successfully.")


if __name__ == "__main__":
    import argparse

    # Create an argument parser
    parser = argparse.ArgumentParser(description="Database Setup Script")
    parser.add_argument(
        "action",
        choices=["create", "drop"],
        help="Specify 'create' to create tables or 'drop' to delete them."
    )

    args = parser.parse_args()

    if args.action == "create":
        create_tables()
    elif args.action == "drop":
        drop_tables()