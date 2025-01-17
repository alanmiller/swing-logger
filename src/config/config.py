import logging
class Config:
    # Path to the mlm2pro-gspro-connect.log file
    LOG_FILE_PATH = 'E:\\MLM-2PRO-GSPro-Connector_V1.04.09\\appdata\\logs\\mlm2pro-gspro-connect.log'
    # Path to the SQLite database
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