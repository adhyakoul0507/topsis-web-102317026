from flask import Flask, request, jsonify
import os
import re
import smtplib
from email.message import EmailMessage
from topsis.topsis import topsis

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)


@app.route("/")
def home():
    return "TOPSIS Web Service Running"


@app.route("/topsis", methods=["POST"])
def run_topsis():

    if 'file' not in request.files:
        return jsonify({"error": "File not provided"}), 400

    file = request.files['file']
    weights = request.form.get("weights")
    impacts = request.form.get("impacts")
    email = request.form.get("email")

    if not weights or not impacts or not email:
        return jsonify({"error": "Missing weights, impacts or email"}), 400

    if not valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    weights_list = weights.split(',')
    impacts_list = impacts.split(',')

    if len(weights_list) != len(impacts_list):
        return jsonify({"error": "Number of weights must equal number of impacts"}), 400

    for i in impacts_list:
        if i not in ['+', '-']:
            return jsonify({"error": "Impacts must be '+' or '-'"}), 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_path = os.path.join(UPLOAD_FOLDER, "result.csv")

    file.save(input_path)

    try:
        topsis(input_path, weights, impacts, output_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    try:
        msg = EmailMessage()
        msg["Subject"] = "Your TOPSIS Result"
        msg["From"] = os.environ.get("EMAIL_USER")
        msg["To"] = email
        msg.set_content("Please find attached your TOPSIS result.")

        with open(output_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="csv", filename="result.csv")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.environ.get("EMAIL_USER"), os.environ.get("EMAIL_PASS"))
            server.send_message(msg)

    except Exception as e:
        return jsonify({"error": "Email sending failed: " + str(e)}), 400

    return jsonify({"message": "Result sent successfully to email!"})


if __name__ == "__main__":
    app.run(debug=True)

