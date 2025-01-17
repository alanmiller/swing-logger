from flask import Flask, jsonify
from db.database import Database

app = Flask(__name__)
db = Database()

@app.route('/lastswing', methods=['GET'])
def get_last_swing():
    last_swing = db.get_last_swing()
    if last_swing:
        # Dynamically construct the JSON response
        column_names = [desc[1] for desc in db.conn.execute('PRAGMA table_info(swings)').fetchall()]
        result = {column_names[i]: last_swing[i] for i in range(len(column_names))}
        return jsonify(result)
    else:
        # Return a 204 No Content status code
        return '', 204

@app.route('/swings/<club>', methods=['GET'])
def get_swings_by_club(club):
    swings = db.get_swings_by_club(club)
    if swings:
        # Dynamically construct the JSON response
        column_names = [desc[1] for desc in db.conn.execute('PRAGMA table_info(swings)').fetchall()]
        results = [{column_names[i]: swing[i] for i in range(len(column_names))} for swing in swings]
        return jsonify(results)
    else:
        # Return a 204 No Content status code
        return '', 204