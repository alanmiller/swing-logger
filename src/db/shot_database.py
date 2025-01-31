import pymysql
from datetime import datetime
import json

class ShotDatabase:
    def __init__(self, host, user, password, database, table):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.table = table
        self.cursor = self.connection.cursor()

    def insert_shot(self, shot_data):
        """Insert shot data from JSON into database"""
        query = f"""
        INSERT INTO {self.table} (
            shot_key, round_key, player_key, player_name, shot_number,
            club_index, distance_to_pin, total_distance,
            ball_speed, total_spin, back_spin, side_spin,
            hla, vla, carry_distance, offline, decent_angle, peak_height,
            club_speed, angle_of_attack, face_to_target, path,
            start_x, start_y, start_z, end_x, end_y, end_z
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        values = (
            shot_data['ShotKey'],
            shot_data['RoundKey'],
            shot_data['PlayerKey'],
            shot_data['PlayerName'],
            shot_data['GlobalShotNumber'],
            shot_data['ClubIndex'],
            shot_data['DistanceToPin'],
            shot_data['TotalDistance'],
            shot_data['BallData']['Speed'],
            shot_data['BallData']['TotalSpin'],
            shot_data['BallData']['BackSpin'],
            shot_data['BallData']['SideSpin'],
            shot_data['BallData']['HLA'],
            shot_data['BallData']['VLA'],
            shot_data['BallData']['CarryDistance'],
            shot_data['BallData']['Offline'],
            shot_data['BallData']['DecentAngle'],
            shot_data['BallData']['PeakHeight'],
            shot_data['ClubData']['Speed'],
            shot_data['ClubData']['AngleOfAttack'],
            shot_data['ClubData']['FaceToTarget'],
            shot_data['ClubData']['Path'],
            shot_data['StartingPOS']['x'],
            shot_data['StartingPOS']['y'],
            shot_data['StartingPOS']['z'],
            shot_data['EndingPOS']['x'],
            shot_data['EndingPOS']['y'],
            shot_data['EndingPOS']['z']
        )

        self.cursor.execute(query, values)
        self.connection.commit()

    def getCursor(self):
        return self.cursor

    def get_last_swing(self):
        """Get the last swing from the database"""
        query = f"SELECT * FROM {self.table} ORDER BY 'created_at' DESC LIMIT 1"
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def get_swings_by_club(self, club):
        """Get all shots for a specific club"""
        # TODO: determin club_index from club_name

        query = f"SELECT * FROM {self.table} WHERE club_index = %s"
        print(f"Query: {query}")
        self.cursor.execute(query, (club,))
        return self.cursor.fetchall()