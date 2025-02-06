import sqlite3

conn = sqlite3.connect('readings.sqlite')

c = conn.cursor()
c.execute('''
          CREATE TABLE blood_pressure
          (id INTEGER PRIMARY KEY ASC, 
           patient_id VARCHAR(250) NOT NULL,
           device_id VARCHAR(250) NOT NULL,
           systolic INTEGER NOT NULL,
           diastolic INTEGER NOT NULL,
           timestamp VARCHAR(100) NOT NULL,
           date_created VARCHAR(100) NOT NULL)
          ''')

c.execute('''
          CREATE TABLE heart_rate
          (id INTEGER PRIMARY KEY ASC, 
           patient_id VARCHAR(250) NOT NULL,
           device_id VARCHAR(250) NOT NULL,
           heart_rate INTEGER NOT NULL,
           timestamp VARCHAR(100) NOT NULL,
           date_created VARCHAR(100) NOT NULL)
          ''')

conn.commit()
conn.close()
