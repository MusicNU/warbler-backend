import flask
import os
import dotenv
import requests
import io

dotenv.load_dotenv()

app = flask.Flask(__name__)

AWS_URL = os.getenv("AUDIVERIS_API_URL", "Failed to find AWS endpoint")
AWS_UPLOAD_URL = AWS_URL + "/upload"
AWS_SCORE_STATUS_URL = AWS_URL + "/status/"

@app.route("/backend-health")
def backend_health_check():
    return "OK", 200

@app.route("/aws-health")
def aws_health_check():
    try: 
        r = requests.get(AWS_URL, timeout=5)
        return r.text, r.status_code
    except Exception as e:
        return {"Error": str(e)}, 503

@app.route("/upload", methods=["POST"])
def upload_score():
    r_json = flask.request.get_json()
    if "file" not in r_json.keys():
        return "Key 'file' with file data is required to upload", 400

    try:
        score = {"file": ("score.pdf", io.BytesIO(r_json["file"]), "application/pdf")}
        r = requests.post(AWS_UPLOAD_URL, files=score)
        return r.text, r.status_code
    except Exception as e:
        return {"Error": str(e)}, 503
    
@app.route("/status")
def get_score_status():
    r_json = flask.request.get_json()
    if "id" not in r_json.keys():
        return "Key 'id' with score ID of a recently uploaded score is required to inspect the status (we don't know which score you want to check!)", 400

    try:
        params = { "id": r_json["id"]}
        r = requests.get(AWS_SCORE_STATUS_URL, params=params)
        print(f"inside api, r.url is {r.url}")
        return r.text, r.status_code
    except Exception as e:
        return {"Error": str(e)}, 503