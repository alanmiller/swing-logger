[![Pylint](https://github.com/alanmiller/swing-logger/actions/workflows/pylint.yml/badge.svg)](https://github.com/alanmiller/swing-logger/actions/workflows/pylint.yml) 
[![Nuitka-Compile](https://github.com/alanmiller/swing-logger/actions/workflows/nuitka.yml/badge.svg)](https://github.com/alanmiller/swing-logger/actions/workflows/nuitka.yml)

![pylint](https://img.shields.io/badge/PyLint-10.00-brightgreen?logo=python&logoColor=white)

## Overview
Swing Logger is a python application that monitors a log file in a background thread for swing data, stores the data to a db, and exposes 2 web-apis  that allow you to retrieve the swing results from a remote computer. The format of the log entries and the JSON structure is specific to 2 use cases.

   - The **mlm2pro-gspro-connect.log** file from springbok's famous [MLM2PRO-GSPro-Connector](https://github.com/springbok/MLM2PRO-GSPro-Connector). When it detects a new swing entry, it stores the details in a local SQLite database. 
   
   - The **output_log.txt** file from [GSPro](https://gsprogolf.com/). When a swing is detected it stores the details to a MySQL database specified on the config.

I wrote this because I wanted to include the swing data in a different application (running on a different host) and I wanted to save a history of swing results in a database for later historical analysis.

### Other Use Cases
This little app is obviously very specific to the log entries used by the [MLM2PRO-GSPro-Connector](https://github.com/springbok/MLM2PRO-GSPro-Connector) and [GSPro](https://gsprogolf.com/) but it might be useful for other uses cases. If you just want to monitor a specific log file on one host for activity and make it available to other hosts via an API, you'd just need to modify the sqlite or mysql schemas and queries in ```src/db/database```, the fields file path in ```config.yaml``` and the parsing logic in ```src/main.py```. And of course you'd want to update the APIs in ```src/api.py```.

Currently there are only 2 APIs defined 

  - ```/lastswing```
       Returns the last recorded swing as json
  - ```/swings/<club>```
       Returns all swings for the given club (I7,I8,...)

## Project Structure
```
swing-logger
│
├── config.yaml              # Configuration settings
├── src
│   ├── main.py              # Main logic for monitoring log files
│   ├── api.py               # API endpoint definitions and logic
│   ├── db
│   │   ├── database.py      # Database interface for using sqlite
│   │   ├── shot_database.py # Database interface for using mysql
│   │   └── shots.sql        # Database schema for mysql
│   └── utils
│       └── logger.py        # Utility functions for logging
├── requirements.txt         # Project dependencies
├── LICENSE                  # License file
└── README.md                # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/alanmiller/swing-logger.git
   cd swing-logger
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Modify the `config.yaml` file to set the log file paths and port & listen address to you liking.

Example config for mlm2gspro mode:

```
data_store: 'sqlite'  
data_source: 'mlm2gspro'
log_level: INFO

# for api binding
port: 9210
listen_address: '0.0.0.0'

log_file_path: 'E:\\MLM-2PRO-GSPro-Connector_V1.04.09\\appdata\\logs\\mlm2pro-gspro-connect.log'
database_path: 'sqlite://E:\\swing-logger\\swing.db'
log_level: DEBUG
json_fields:
  - new_shot
  - club
  - speed
  - spin_axis
  - total_spin
  - hla
  - vla
  - club_speed
  - back_spin
  - side_spin
  - path
  - face_to_target
  - angle_of_attack
  - speed_at_impact
monitored_log_entries:
  - "GSProConnect: Success"
```

Example config for gspro mode:

```
data_store: 'mysql'  
data_source: 'gspro' 
log_level: INFO

# for api binding
port: 9210
listen_address: '0.0.0.0'

# for gspro mode (use mysql)
gspro:
  log_file_path: 'C:\\Users\\my-user-name\\AppData\\LocalLow\\GSPro\\GSPro\\output_log.txt'
mysql:
  host: '10.20.30.40'
  db: 'swingstudio'
  table: 'shots'
  user: 'sql-user'
  pass: 'sql-pass'
```

## Usage

### Run the swing logger application using the following command:

The `--conf` argument is optional and will default to config.yaml in the current directory if present.

```
python src/main.py  [ --conf <path to config.yaml> ]
```

### Call the APIs

After some new swings have been logged to mlm2pro-gspro-connect.log, you can call the apis.

#### Get the last swing

```
[user@host] curl http://localhost:9210/lastswing
{
  "angle_of_attack": -2.82,
  "back_spin": 9032.0,
  "club": "I9",
  "club_speed": 84.19,
  "face_to_target": -0.94,
  "hla": -0.04,
  "id": 4,
  "path": -2.13,
  "side_spin": 199.0,
  "speed": 100.07,
  "speed_at_impact": 84.19,
  "spin_axis": 0.26,
  "timestamp": "2025-01-17:17:07:00,000",
  "total_spin": 8000.6,
  "vla": 18.89
}
```
#### Get all 4-iron swings

```
[user@host] http://localhost:9210/swings/I4
[
  {
    "angle_of_attack": -2.82,
    "back_spin": 9032.0,
    "club": "I4",
    "club_speed": 84.19,
    "face_to_target": -0.94,
    "hla": -1.04,
    "id": 2,
    "path": -2.13,
    "side_spin": 199.0,
    "speed": 110.07,
    "speed_at_impact": 84.19,
    "spin_axis": 1.26,
    "timestamp": "2025-01-16:11:11:11,111",
    "total_spin": 9034.6,
    "vla": 18.89
  },
  {
    "angle_of_attack": -2.82,
    "back_spin": 9032.0,
    "club": "I4",
    "club_speed": 84.19,
    "face_to_target": -0.94,
    "hla": -1.04,
    "id": 3,
    "path": -2.13,
    "side_spin": 199.0,
    "speed": 110.07,
    "speed_at_impact": 84.19,
    "spin_axis": 1.26,
    "timestamp": "2025-01-16:11:11:11,111",
    "total_spin": 9034.6,
    "vla": 18.89
  }
]
```

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Copyright
Copyright (c) 2025 Alan Miller
