""" Database module for PostgreSQL operations """
import psycopg2

class ShotDatabase:
    """ Class to handle database operations """
    def __init__(self, settings):
        """ Initialize the database connection """            
        self.connection = psycopg2.connect(
            host=settings['postgres']['host'],
            user=settings['postgres']['user'],
            password=settings['postgres']['pass'],
            database=settings['postgres']['db'],
            port=settings['postgres'].get('port', 5432)
        )
        self.table = settings['postgres']['table']
        self.cursor = self.connection.cursor()

    def insert_shot(self, shot_data):
        """Insert shot data from JSON into database"""
        
        # Check if this shot already exists by gspro_shot_id
        gspro_shot_id = shot_data.get('gspro_shot_id')
        if gspro_shot_id:
            check_query = "SELECT 1 FROM {} WHERE gspro_shot_id = %s LIMIT 1".format(self.table)
            self.cursor.execute(check_query, (gspro_shot_id,))
            if self.cursor.fetchone():
                # Shot already exists, skip insert
                import logging
                logging.debug(f"Skipping duplicate shot with gspro_shot_id: {gspro_shot_id}")
                return False
        
        query = """
        INSERT INTO {} (
            gspro_shot_id, club, device_id, units, api_version,
            ball_speed, spin_axis, total_spin, hla, vla, backspin, sidespin, carry_distance,
            offline, decent_angle, peak_height,
            club_speed, angle_of_attack, face_to_target, club_lie, club_loft, club_path,
            speed_at_impact, vertical_face_impact, horizontal_face_impact, closure_rate,
            contains_ball_data, contains_club_data, launch_monitor_ready, 
            launch_monitor_ball_detected, is_heartbeat,
            total_distance, distance_to_pin, face_to_path, smash_factor, dynamic_loft
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        """.format(self.table)

        ball_data = shot_data.get('BallData', {})
        club_data = shot_data.get('ClubData', {})
        shot_options = shot_data.get('ShotDataOptions', {})
        gspro_data = shot_data.get('GSProData', {})

        values = (
            shot_data.get('gspro_shot_id'),
            shot_data.get('ShotNumber'),
            shot_data.get('DeviceID'),
            shot_data.get('Units'),
            shot_data.get('APIversion'),
            ball_data.get('Speed'),
            ball_data.get('SpinAxis'),
            ball_data.get('TotalSpin'),
            ball_data.get('HLA'),
            ball_data.get('VLA'),
            ball_data.get('Backspin'),
            ball_data.get('SideSpin'),
            ball_data.get('CarryDistance'),
            ball_data.get('Offline'),
            ball_data.get('DecentAngle'),
            ball_data.get('PeakHeight'),
            club_data.get('Speed'),
            club_data.get('AngleOfAttack'),
            club_data.get('FaceToTarget'),
            club_data.get('Lie'),
            club_data.get('Loft'),
            club_data.get('Path'),
            club_data.get('SpeedAtImpact'),
            club_data.get('VerticalFaceImpact'),
            club_data.get('HorizontalFaceImpact'),
            club_data.get('ClosureRate'),
            shot_options.get('ContainsBallData'),
            shot_options.get('ContainsClubData'),
            shot_options.get('LaunchMonitorIsReady'),
            shot_options.get('LaunchMonitorBallDetected'),
            shot_options.get('IsHeartBeat'),
            gspro_data.get('TotalDistance'),
            gspro_data.get('DistanceToPin'),
            gspro_data.get('FaceToPath'),
            gspro_data.get('SmashFactor'),
            gspro_data.get('DynamicLoft')
        )

        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            raise e

    def get_cursor(self):
        """Return the cursor"""
        return self.cursor

    def get_last_swing(self):
        """Get the last swing from the database"""
        query = "SELECT * FROM {} ORDER BY gspro_shot_id DESC LIMIT 1".format(self.table)
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def get_swings_by_club(self, club_index, limit=25):
        """Get all shots for a specific club by club_index"""
        query = "SELECT * FROM {} WHERE club_index = %s LIMIT %s".format(self.table)
        self.cursor.execute(query, (club_index, limit))
        results = self.cursor.fetchall()
        return results
