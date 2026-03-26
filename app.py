from flask import Flask, jsonify, request, render_template
import os
from database import get_db, init_db
from algorithms import get_prediction
from scraper import scrape_summary

app = Flask(__name__)

# Initialize database if it doesn't exist (important for Render/Gunicorn)
if not os.path.exists('vietlott.db'):
    init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    raw_game_type = data.get('game_type', 'mega')
    algo_type = data.get('algo_type', 'ensemble')
    
    # Normalize game_type to simple identifiers used by the prediction engine
    if 'mega' in raw_game_type.lower():
        game_type = 'mega'
    elif 'power' in raw_game_type.lower():
        game_type = 'power'
    else:
        game_type = raw_game_type
    
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

@app.route('/api/latest_info', methods=['GET'])
def latest_info():
    try:
        mega_info = scrape_summary('mega')
        power_info = scrape_summary('power')
        return jsonify({
            "success": True, 
            "mega": mega_info,
            "power": power_info
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
