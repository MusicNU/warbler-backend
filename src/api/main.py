import flask
import os
import dotenv
import requests
import boto3
import io
import pathlib
from datetime import datetime
import uuid

from .modules import valid_uuid, s3_object_exists

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
AWS_BUCKET = os.getenv("AWS_BUCKET", "Failed to get an AWS bucket")

# lazy S3 client, initialized on first use 
s3 = None

def get_s3_client():
    """Lazily create and cache an S3 client using AWS_PROFILE ."""
    global s3
    if s3 is not None:
        return s3

    try:
        # Try AWS_PROFILE first (from .env), then AWS_PROFILE (standard boto3 env var)
        profile = os.getenv("AWS_PROFILE")
        session = boto3.Session(profile_name=profile)
        
        s3 = session.client('s3')
        return s3
    except Exception as e:
        print(f"Warning: Failed to create S3 client: {str(e)}")
        print("You may not have AWS_PROFILE set correctly in your .env file")
        return None

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

        file_name = f"{uuid.uuid4()}.pdf"

        files = {"file": (file_name, uploaded_score.stream, uploaded_score.content_type or "application/pdf")}
        r = requests.post(AWS_UPLOAD_URL, files=files)
        try:
            return r.json(), r.status_code
        except:
            return r.text, r.status_code
    except Exception as e:
        return {"Error": str(e)}, 503
    
@app.route("/upload/wav", methods=["POST"])
def upload_wav():
    """Uploads a WAV file to S3."""

    if "file" not in flask.request.files:
        return "Key 'file' with file data is required to upload", 400
    try:
        uploaded_wav = flask.request.files["file"]
        id = str(uuid.uuid4())
        file_name = f"{id}.wav"

        s3 = get_s3_client()
        if s3 is None:
            return {"Error": "Unable to locate credentials"}, 503
        
        s3.upload_fileobj(uploaded_wav.stream, AWS_BUCKET, file_name)
        response = flask.jsonify({"id": id})
        return response, 200
    except Exception as e:
        return {"Error": str(e)}, 503

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
    
    if not valid_uuid(score_id):
        return {"Error": f"Invalid UUID for mxl ID: {score_id}"}, 400
    
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
    wav_id = flask.request.args.get("id", None)
    if wav_id is None:
        return "Key 'id' with score ID of a recently uploaded wav is required to download the processed wav", 400

    if not valid_uuid(wav_id):
        return {"Error": f"Invalid UUID for wav ID: {wav_id}"}, 400

    s3 = get_s3_client()
    if s3 is None:
        return {"Error": "Unable to locate credentials"}, 503
    
    try:
        file_name = f"{wav_id}.wav"
        data = s3.get_object(Bucket=AWS_BUCKET, Key=file_name)['Body'].read()

        return flask.send_file(
            io.BytesIO(data),
            as_attachment=True,
            download_name=file_name,
            mimetype="audio/wav"
        )
    except Exception as e:
        return {"Error": str(e)}, 503
    
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
    
    if not valid_uuid(score_id):
        return {"Error": f"Invalid UUID for mxl ID: {score_id}"}, 400

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
    Takes in id_wav and id_mxl and returns analysis of performance
    
    Kind of the the entire point of this API

    Make sure that the pdf has been processed and converted to an mxl file! (check the score-status endpoint)
    """
    wav_id = flask.request.json.get("id_wav", None)
    mxl_id = flask.request.json.get("id_mxl", None)

    if wav_id is None or mxl_id is None:
        return "Both 'id_wav' and 'id_mxl' are required in the body", 400

    if not valid_uuid(wav_id):
        return {"Error": f"Invalid UUID for wav ID: {wav_id}"}, 400
    if not valid_uuid(mxl_id):
        return {"Error": f"Invalid UUID for mxl ID: {mxl_id}"}, 400
    
    print("Passed checks, about to send requests to download endpoints...")
    try:
        r_wav = requests.get(APP_WAV_DOWNLOAD_URL, params={"id": wav_id})
        r_mxl = requests.get(APP_MXL_DOWNLOAD_URL, params={"id": mxl_id})

        assert r_wav.status_code == 200, f"Expected 200 status code when downloading previously uploaded wav file, got {r_wav.status_code}"
        assert r_mxl.status_code == 200, f"Expected 200 status code when downloading previously uploaded mxl file, got {r_mxl.status_code}"

        print("Download requests for wav an mxl succeeded. Storing files temporarily for analysis...")
        with open("score.mxl", "wb") as f:
            f.write(r_mxl.content)
        print("Wrote to score.mxl")
        with open("performance.wav", "wb") as f:
            f.write(r_wav.content)
        print("Wrote to performance.wav")

        print("Performing analysis...")
        # insert analysis
        print("Size of score.mxl:", os.path.getsize("score.mxl"))
        print("Size of performance.wav:", os.path.getsize("performance.wav"))

        # cleanup files after
        os.remove("score.mxl")
        os.remove("performance.wav")

        return "Dummy feedback", 200  
    except Exception as e:
        return {"Error": str(e)}, 503
