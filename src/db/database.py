""" Database module for handling database operations """
import sqlite3
class Database:
    """ Class to handle database operations """
    def __init__(self, db_path='swing.db'):
        """ Initialize the database with the given path """
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        """ Create the swings table if it does not exist """
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS swings (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    timestamp TEXT,
                                    club TEXT,
                                    speed REAL,
                                    spin_axis REAL,
                                    total_spin REAL,
                                    hla REAL,
                                    vla REAL,
                                    club_speed REAL,
                                    back_spin REAL,
                                    side_spin REAL,
                                    path REAL,
                                    face_to_target REAL,
                                    angle_of_attack REAL,
                                    speed_at_impact REAL
                                )''')
            self.conn.commit()

    def insert_swing(self, swing_data):
        """ Insert the swing data into the database """
        with self.conn:
            self.conn.execute('''INSERT INTO swings (timestamp,  club, speed, spin_axis,
                              total_spin, hla, vla, club_speed, back_spin, side_spin, 
                              path, face_to_target, angle_of_attack, speed_at_impact)
                              VALUES (:timestamp, :club, :speed, :spin_axis, :total_spin,
                              :hla, :vla, :club_speed, :back_spin, :side_spin, :path, 
                              :face_to_target, :angle_of_attack, :speed_at_impact)''',
                            swing_data)
            self.conn.commit()

    def swing_exists(self, timestamp):
        """ Check if a swing with the given timestamp exists in the database """
        cursor = self.conn.cursor()
        cursor.execute('''SELECT 1 FROM swings WHERE timestamp = ? LIMIT 1''', (timestamp,))
        return cursor.fetchone() is not None

    def get_last_swing(self):
        """ Get the last swing from the database """
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM swings ORDER BY id DESC LIMIT 1''')
        return cursor.fetchone()

    def get_swings_by_club(self, club):
        """ Get all swings for a given club from the database """
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM swings WHERE club = ?''', (club,))
        return cursor.fetchall()

    def close(self):
        """ Close the database connection """
        self.conn.close()
