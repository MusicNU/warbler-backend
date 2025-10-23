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
AWS_GET_MXL_URL = AWS_URL + "/download/"

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

@app.route("/upload", methods=["POST"])
def upload_score():
    """Uploads score to Audiveris. The score will then enter the 'processing' phase, where it will be converted from a pdf to mxl file
    Expects a binary file in pdf format as input. The pdf is expected to be a score, otherwise the the download endpoint will likely fail
     
       """
    if "file" not in flask.request.files:
        return "Key 'file' with file data is required to upload", 400
    try:
        uploaded_score = flask.request.files["file"]
        files = {"file": (uploaded_score.filename or "score.pdf", uploaded_score.stream, uploaded_score.content_type or "application/pdf")}
        r = requests.post(AWS_UPLOAD_URL, files=files)
        try:
            return r.json(), r.status_code
        except:
            return r.text, r.status_code
    except Exception as e:
        return {"Error": str(e)}, 503
    
@app.route("/status")
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
        print(f"Received request args: {score_id}")
        r = requests.get(AWS_SCORE_STATUS_URL + str(score_id))
        print(f"Sent request to {r.url}")
        print(f"Resulting text: {r.text}")
        try:
            return r.json(), r.status_code
        except:
            return r.text, r.status_code
    except Exception as e:
        return {"Error": str(e)}, 503

@app.route("/download")
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