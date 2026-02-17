from flask import Flask, render_template, request, send_file, jsonify
import os
import re
from topsis.topsis import topsis

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/topsis", methods=["POST"])
def run_topsis():

    file = request.files.get("file")
    weights = request.form.get("weights")
    impacts = request.form.get("impacts")

    if not file or not weights or not impacts:
        return jsonify({"error": "File, weights, and impacts are required."}), 400

    weights_list = weights.split(',')
    impacts_list = impacts.split(',')

    if len(weights_list) != len(impacts_list):
        return jsonify({"error": "Number of weights must equal number of impacts."}), 400

    for i in impacts_list:
        if i.strip() not in ['+', '-']:
            return jsonify({"error": "Impacts must be '+' or '-'."}), 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_path = os.path.join(UPLOAD_FOLDER, "result.csv")

    file.save(input_path)

    try:
        topsis(input_path, weights, impacts, output_path)
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

    return send_file(
        output_path,
        mimetype="text/csv",
        as_attachment=True,
        download_name="topsis_result.csv"
    )
