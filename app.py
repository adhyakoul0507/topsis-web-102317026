from flask import Flask, render_template, request
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
    return render_template("index.html")


@app.route("/topsis", methods=["POST"])
def run_topsis():

    file = request.files.get("file")
    weights = request.form.get("weights")
    impacts = request.form.get("impacts")
    email = request.form.get("email")

    if not file or not weights or not impacts or not email:
        return "All fields are required."

    if not valid_email(email):
        return "Invalid email format."

    weights_list = weights.split(',')
    impacts_list = impacts.split(',')

    if len(weights_list) != len(impacts_list):
        return "Number of weights must equal number of impacts."

    for i in impacts_list:
        if i not in ['+', '-']:
            return "Impacts must be '+' or '-'."

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_path = os.path.join(UPLOAD_FOLDER, "result.csv")

    file.save(input_path)

    try:
        topsis(input_path, weights, impacts, output_path)
    except Exception as e:
        return f"Error processing file: {str(e)}"

    try:
        msg = EmailMessage()
        msg["Subject"] = "Your TOPSIS Result"
        msg["From"] = os.environ.get("EMAIL_USER")
        msg["To"] = email
        msg.set_content("Please find attached your TOPSIS result.")

        with open(output_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="csv",
                filename="result.csv"
            )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                os.environ.get("EMAIL_USER"),
                os.environ.get("EMAIL_PASS")
            )
            server.send_message(msg)

    except Exception as e:
        return f"Email sending failed: {str(e)}"

    return "Result sent successfully to your email!"

