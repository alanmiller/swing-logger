""" This module contains the API endpoints for the Flask application. """
from flask import Flask, jsonify

def create_app(db,db_type):
    """ Create a Flask app for the provided database """
    app = Flask(__name__)
    app.db = db
    app.db_type = db_type

    @app.route('/lastswing', methods=['GET'])
    def get_last_swing():
        """ Get the last swing from the database """
        payload = ''
        code = 204
        pragma = 'PRAGMA table_info(swings)'
        last_swing = db.get_last_swing()
        if last_swing:
            if app.db_type == 'sqlite':
                # Dynamically construct the JSON response
                column_names = [desc[1] for desc in db.conn.execute(pragma).fetchall()]
            elif app.db_type == 'mysql':
                cursor = db.get_cursor()
                cursor.execute("SHOW COLUMNS FROM shots")
                column_names = [row[0] for row in cursor.fetchall()]
            result = {column_names[i]: last_swing[i] for i in range(len(column_names))}
            payload = jsonify(result)
            code = 200
        return payload, code

    @app.route('/swings/<club>', methods=['GET'])
    def get_swings_by_club(club):
        """ Get all swings for a given club from the database """
        payload = ''
        code = 204
        pragma = 'PRAGMA table_info(swings)'
        swings = db.get_swings_by_club(club)
        if swings:
            # Dynamically construct the JSON response
            if app.db_type == 'sqlite':
                column_names = [desc[1] for desc in db.conn.execute(pragma).fetchall()]
            elif app.db_type == 'mysql':
                cursor = db.get_cursor()
                cursor.execute("SHOW COLUMNS FROM shots")
                column_names = [row[0] for row in cursor.fetchall()]
            results = [
                {column_names[i]: swing[i] for i in range(len(column_names))}
                    for swing in swings
            ]
            payload = jsonify(results)
            code = 200
        return payload, code
    return app
