import flask
import os
import dotenv
import requests
import boto3
import io
import pathlib
from datetime import datetime

dotenv.load_dotenv()

app = flask.Flask(__name__)

# correct the path to the aws credentials file
os.environ['AWS_SHARED_CREDENTIALS_FILE'] = str(pathlib.Path(__file__).parent.parent.parent / ".aws" / "credentials")

# Endpoints for this API
APP_URL = os.getenv("API_URL", "http://127.0.0.1:5000")
APP_AWS_HEALTH_URL = APP_URL + "/aws-health"
APP_HEALTH_URL = APP_URL + "/app-health"
APP_UPLOAD_PDF_URL = APP_URL + "/upload/pdf"
APP_UPLOAD_WAV_URL = APP_URL + "/upload/wav"
APP_SCORE_STATUS_URL = APP_URL + "/score-status"
APP_MXL_DOWNLOAD_URL = APP_URL + "/download/mxl"
APP_WAV_DOWNLOAD_URL = APP_URL + "/download/wav"
APP_ANALYZE_PERFORMANCE_URL = APP_URL + "/analyze-performance"

# Endpoints for AWS audiveris hosting (used internally here by this API, not to be used directly by clients. Instead, use the endpoints above)
AWS_URL = os.getenv("AUDIVERIS_API_URL", "Failed to find AWS endpoint")
AWS_UPLOAD_URL = AWS_URL + "/upload"
AWS_SCORE_STATUS_URL = AWS_URL + "/status/"
AWS_GET_MXL_URL = AWS_URL + "/download/"
AWS_PROFILE_NAME = os.getenv("AWS_PROFILE_NAME", "AWS profile name does not exist")
AWS_BUCKET = os.getenv("AWS_BUCKET", "Failed to get an AWS bucket")

# session = boto3.Session(profile_name=AWS_PROFILE_NAME)
# s3 = session.client('s3')

@app.route("/app-health")
def backend_health_check():
    """Check health of backend api endpoints"""
    return "OK", 200

@app.route("/aws-health")
def aws_health_check():
    """Check health of the Audiveris AWS hosting"""
    try: 
        r = requests.get(AWS_URL, timeout=5)
        return r.text, r.status_code
    except Exception as e:
        return {"Error": str(e)}, 503

@app.route("/upload/pdf", methods=["POST"])
def upload_score():
    """Uploads score to Audiveris. The score will then enter the 'processing' phase, where it will be converted from a pdf to mxl file
    Expects a binary file in pdf format as input. The pdf is expected to be a score, otherwise the the download endpoint will likely fail
     
       """
    if "file" not in flask.request.files:
        return "Key 'file' with file data is required to upload", 400
    try:
        uploaded_score = flask.request.files["file"]

        alternate_name = f"{datetime.now()}.pdf"
        files = {"file": (uploaded_score.filename or alternate_name, uploaded_score.stream, uploaded_score.content_type or "application/pdf")}
        r = requests.post(AWS_UPLOAD_URL, files=files)
        try:
            return r.json(), r.status_code
        except:
            return r.text, r.status_code
    except Exception as e:
        return {"Error": str(e)}, 503
    
# @app.route("/upload/wav", methods=["POST"])
# def upload_wav():
#     """Uploads a WAV file to S3."""

#     if "file" not in flask.request.files:
#         return "Key 'file' with file data is required to upload", 400
#     try:
#         uploaded_wav = flask.request.files["file"]
#         file_name = uploaded_wav.filename or f"{datetime.now()}.wav"
#         s3.upload_fileobj(uploaded_wav, AWS_BUCKET, file_name)
#         return f"Successfully uploaded {file_name} to S3", 200
#     except Exception as e:
#         return {"Error": str(e)}, 503

@app.route("/download/mxl")
def download_score():
    """
    Returns the .mxl file for the previously uploaded pdf. 
    Note you must have used the upload endpoint to have uploaded the score already, and you should check if the score is done processing at the status endpoint

    The content body contains the binary for the mxl file
    """
    score_id = flask.request.args.get("id", None)
    if score_id is None:
        return "Key 'id' with score ID of a recently uploaded score is required to download the processed score", 400
    
    try:
        r = requests.get(AWS_GET_MXL_URL + score_id)

        return flask.send_file(
            io.BytesIO(r.content), 
            as_attachment=True,
            download_name=f"score-{score_id}.mxl",
            mimetype=r.headers.get("Content-Type")
        )
    except Exception as e:
        return {"Error": str(e)}, 503
    
@app.route("/download/wav")
def download_wav():
    """
    Returns the .wav file for the previously uploaded wav. 
    Note you must have used the upload endpoint to have uploaded the wav already
    The content body contains the binary for the wav file
    """
    score_id = flask.request.args.get("id", None)
    if score_id is None:
        return "Key 'id' with score ID of a recently uploaded wav is required to download the processed wav", 400
    return "Not yet implemented", 501

@app.route("/score-status")
def get_score_status():
    """Check the status of a PREVIOUSLY uploaded score. 

    Include the score's id (returned from upload endpoint) in the params
    
    The "status" key in the JSON response from the POST request indicates whether the processing is complete
    - If `response['status'] == 'processing'` -> still processing
    - If `response['status'] == 'completed'` -> finished processing, can now query download endpoint to retrieve file
    - If `response['status'] == 'error'` -> some error occured, check the 'message' header
    """
    score_id = flask.request.args.get("id", None)
    if score_id is None:
        return "Key 'id' with score ID of a recently uploaded score is required to inspect the status (we don't know which score you want to check!)", 400

    try:
        r = requests.get(AWS_SCORE_STATUS_URL + str(score_id))
        print(f"Sent request to {r.url}")
        print(f"Resulting text: {r.text}")
        try:
            return r.json(), r.status_code
        except:
            return r.text, r.status_code
    except Exception as e:
        return {"Error": str(e)}, 503

@app.route("/analyze-performance", methods=["POST"])
def analyze_performance():
    """
    Takes in uploaded wav and mxl file and returns analysis of performance
    
    Kind of the the entire point of this API
    """
    # if "file" not in flask.request.files
    return "Not yet implemented", 501