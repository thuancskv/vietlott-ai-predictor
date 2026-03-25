from flask import Flask, jsonify, request, render_template
import os
from database import get_db, init_db
from algorithms import get_prediction

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    game_type = data.get('game_type', 'mega')
    algo_type = data.get('algo_type', 'ensemble')
    
    conn = get_db()
    try:
        prediction = get_prediction(conn, game_type, algo_type)
        prediction = [int(p) for p in prediction]
        return jsonify({"success": True, "prediction": prediction, "algorithm": algo_type})
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "trace": traceback.format_exc()})
    finally:
        conn.close()

if __name__ == '__main__':
    if not os.path.exists('vietlott.db'):
        init_db()
    app.run(debug=True, port=5000)
