# Swing Logger

## Overview
Swing Logger is a python application that monitors an mlm2pro-gspro-connect.log file from springbok's famous [MLM2PRO-GSPro-Connector](https://github.com/springbok/MLM2PRO-GSPro-Connector) in a background thread for swing data. When it detects a new swing entry, it stores the details in a SQLite database. On the frontend it exposes 2 web-apis that allow you to retrieve the swing results from a remote computer. 

I wrote this because I wanted to include the swing data in a different application (running on a different host) and I wanted to save a history of swing results in a database for later historical analysis.

### Other Use Cases
This little app is obviously very specific to the log entries used by the [MLM2PRO-GSPro-Connector](https://github.com/springbok/MLM2PRO-GSPro-Connector) but it might be useful for other uses cases. If you just want to monitor a specific log file on one host for activity and make it available to other hosts via an API, you'd just need to modify the sqlite table and queries in ```src/db/database```, the fields file path in ```src/config/config.py``` and the parsing logic in ```src/main/py```. And of course you'd want to update the APIs in ```src/api.py``.

Currently there are only 2 APIs defined 

  - ```/lastswing```
       Returns the last recorded swing as json
  - ```/swings/<club>```
       Returns all swings for the given club (I7,I8,...)

## Project Structure
```
swing-logger
├── src
│   ├── main.py       # Main logic for monitoring log files
│   ├── api.py        # API endpoint definitions and logic
│   ├── db
│   │   └── database.py      # Database connection and operations
│   ├── utils
│   │   └── logger.py        # Utility functions for logging
│   └── config
│       └── config.py        # Configuration settings
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd swing-logger
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Modify the `src/config/config.py` file to set the log file path and database connection details according to your environment.

Example config.py:

```
class Config:
    # Path to the mlm2pro-gspro-connect.log file
    LOG_FILE_PATH = 'E:\\MLM-2PRO-GSPro-Connector_V1.04.09\\appdata\\logs\\mlm2pro-gspro-connect.log'
    # Path to the sqlite file (will be created) if it does not already exist
    DATABASE_PATH = 'sqlite://E:\\swing-logger\\swing.db'
    # Log level for the logger
    LOG_LEVEL = logging.INFO
    # Fields to be extracted from the JSON log entry
    JSON_FIELDS = [
        'new_shot', 'club', 'speed', 
        'spin_axis', 'total_spin', 'hla', 'vla', 'club_speed', 'back_spin', 
        'side_spin', 'path', 'face_to_target', 'angle_of_attack', 'speed_at_impact'
    ]
    # Log entries to be monitored
    MONITORED_LOG_ENTRIES = ["GSProConnect: Success"]
```

## Usage

### Run the swing logger application using the following command:

```
python src/main.py
```

### Call the APIs

After some new swings have been logged to mlm2pro-gspro-connect.log, you can call the apis.

#### Get the last swing

```
[user@host] curl http://localhost:5000/lastswing
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
[user@host] http://localhost:5000/swings/I4
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
This project is licensed under the MIT License. See the LICENSE file for details.

## Copyright
Copyright (c) 2025 Alan Miller