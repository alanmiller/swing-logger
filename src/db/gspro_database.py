""" GSPro Database handler for monitoring shot data """
import sqlite3
import json
import logging
from datetime import datetime

class GSProDatabaseHandler:
    """ Class to handle GSPro database operations """
    
    def __init__(self, config, target_db=None):
        self.config = config
        # Get GSPro database path from config, with default fallback
        self.db_path = config.get('gspro_db_path', 
                                   r"C:\Users\alanm\AppData\LocalLow\GSPro\GSPro\GSPro.db")
        self.last_shot_id = 0
        self.last_round_id = 0
        self.target_db = target_db
        
        # Try to get the last processed shot ID from the target database
        if target_db:
            try:
                self.last_shot_id = self._get_last_processed_shot_id()
                logging.info(f"Resuming from last processed GSPro shot ID: {self.last_shot_id}")
            except Exception as e:
                logging.warning(f"Could not get last processed shot ID, starting from 0: {e}")
                self.last_shot_id = 0
        
        logging.info(f"GSProDatabaseHandler initialized with database: {self.db_path}")
    
    def _get_last_processed_shot_id(self):
        """ Get the last processed GSPro shot ID from the target database """
        try:
            cursor = self.target_db.get_cursor()
            table = self.target_db.table
            
            # Query for the maximum gspro_shot_id that we've already stored
            cursor.execute(f"SELECT MAX(shot_number) FROM {table} WHERE shot_number ~ '^[0-9]+$'")
            result = cursor.fetchone()
            
            if result and result[0]:
                # The shot_number field contains the GSPro shot ID
                # We need to extract the numeric ID from the shot data
                # For now, let's query differently
                pass
            
            # Better approach: add a column to track gspro_shot_id
            # For now, return 0 to process all
            return 0
            
        except Exception as e:
            logging.error(f"Error getting last processed shot ID: {e}")
            return 0
    
    def get_new_shots(self):
        """ Get new shots from DrivingRangeShot table """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get shots newer than last processed
            cursor.execute("""
                SELECT ID, DateCreated, ShotData 
                FROM DrivingRangeShot 
                WHERE ID > ?
                ORDER BY ID ASC
            """, (self.last_shot_id,))
            
            shots = cursor.fetchall()
            
            if shots:
                # Update last processed ID
                self.last_shot_id = shots[-1][0]
                logging.info(f"Found {len(shots)} new shots")
            
            conn.close()
            return shots
            
        except Exception as e:
            logging.error(f"Error getting new shots: {e}")
            return []
    
    def get_new_rounds(self):
        """ Get new rounds from PlayerGSPHCv1 table """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get rounds newer than last processed
            cursor.execute("""
                SELECT ID, UserGuid, RoundID, CreatedDate, RoundHandicap, CalculatedHandicap
                FROM PlayerGSPHCv1 
                WHERE ID > ?
                ORDER BY ID ASC
            """, (self.last_round_id,))
            
            rounds = cursor.fetchall()
            
            if rounds:
                # Update last processed ID
                self.last_round_id = rounds[-1][0]
                logging.info(f"Found {len(rounds)} new rounds")
            
            conn.close()
            return rounds
            
        except Exception as e:
            logging.error(f"Error getting new rounds: {e}")
            return []
    
    def get_player_clubs(self, user_guid=None):
        """ Get player club configuration """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_guid:
                cursor.execute("SELECT Clubs FROM PlayerBag WHERE UserGuid = ?", (user_guid,))
            else:
                cursor.execute("SELECT Clubs FROM PlayerBag LIMIT 1")
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
            return None
            
        except Exception as e:
            logging.error(f"Error getting player clubs: {e}")
            return None
    
    def process_shot_data(self, shot_data_str):
        """ Process and parse shot data """
        if not shot_data_str:
            return None
            
        try:
            # Try to parse as JSON
            gspro_data = json.loads(shot_data_str)
            
            # Transform GSPro data to match your existing database schema
            transformed_data = {
                'DeviceID': 'GSPro',
                'Units': 'Yards',
                'ShotNumber': gspro_data.get('club', 'Unknown'),  # Use club as identifier
                'APIversion': '1',
                'BallData': {
                    'Speed': gspro_data.get('BallSpeed', 0),
                    'SpinAxis': gspro_data.get('rawSpinAxis', 0),
                    'TotalSpin': abs(gspro_data.get('BackSpin', 0)) + abs(gspro_data.get('SideSpin', 0)),
                    'HLA': gspro_data.get('HLA', 0),
                    'VLA': gspro_data.get('VLA', 0),
                    'Backspin': gspro_data.get('BackSpin', 0),
                    'SideSpin': gspro_data.get('SideSpin', 0),
                    'CarryDistance': gspro_data.get('Carry', 0),
                    'Offline': gspro_data.get('Offline', 0),
                    'DecentAngle': gspro_data.get('Decent', 0),
                    'PeakHeight': gspro_data.get('PeakHeight', 0)
                },
                'ClubData': {
                    'Speed': gspro_data.get('ClubSpeed', 0),
                    'AngleOfAttack': gspro_data.get('AoA', 0),
                    'FaceToTarget': gspro_data.get('FaceToTarget', 0),
                    'Lie': gspro_data.get('Lie', 0),
                    'Loft': gspro_data.get('Loft', 0),
                    'Path': gspro_data.get('Path', 0),
                    'SpeedAtImpact': gspro_data.get('ClubSpeed', 0),
                    'VerticalFaceImpact': gspro_data.get('VI', 0),
                    'HorizontalFaceImpact': gspro_data.get('HI', 0),
                    'ClosureRate': gspro_data.get('CR', 0)
                },
                'ShotDataOptions': {
                    'ContainsBallData': True,
                    'ContainsClubData': True,
                    'LaunchMonitorIsReady': True,
                    'LaunchMonitorBallDetected': True,
                    'IsHeartBeat': False
                },
                # Additional GSPro-specific data
                'GSProData': {
                    'Club': gspro_data.get('club'),
                    'TotalDistance': gspro_data.get('TotalDistance', 0),
                    'DistanceToPin': gspro_data.get('DistanceToPin', 0),
                    'FaceToPath': gspro_data.get('FaceToPath', 0),
                    'SmashFactor': gspro_data.get('SmashFactor', 0),
                    'DynamicLoft': gspro_data.get('DynamicLoft', 0)
                }
            }
            
            return transformed_data
            
        except json.JSONDecodeError:
            logging.error(f"Failed to parse shot data as JSON: {shot_data_str}")
            return None
    
    def check_for_new_data(self):
        """ Check for new shots and rounds """
        new_shots = []
        new_rounds = []
        
        try:
            # Check for new shots
            raw_shots = self.get_new_shots()
            for shot in raw_shots:
                shot_id, date_created, shot_data_str = shot
                processed_data = self.process_shot_data(shot_data_str)
                if processed_data:
                    processed_data['gspro_shot_id'] = shot_id
                    processed_data['gspro_date_created'] = date_created
                    new_shots.append(processed_data)
            
            # Check for new rounds
            new_rounds = self.get_new_rounds()
            
        except Exception as e:
            logging.error(f"Error checking for new data: {e}")
        
        return new_shots, new_rounds