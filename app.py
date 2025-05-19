from flask import Flask, jsonify, request
import supabase_client
import usd_volume_analysis
import alchemy
from flask_cors import CORS
from dotenv import load_dotenv



app = Flask(__name__)
CORS(app)
load_dotenv()

@app.route("/api/volume")
def get_volume():
    # Query all rows from usd_volume
    formatted_data = supabase_client.get_usd_volume_date()
    return jsonify(formatted_data)


#alchemy is used to get transaction
@app.route("/api/wallet/<wallet>")
def wallet(wallet):
    try:
        data = alchemy.analyze_wallet(wallet)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

#backfills data in supabase for volume api    
@app.route("/api/backfill")
def backfill():
    try:
        usd_volume_analysis.run_single_day()
        return jsonify({"success": "backfill done"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True)
