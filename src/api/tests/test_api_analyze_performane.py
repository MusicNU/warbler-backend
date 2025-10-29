from dotenv import load_dotenv
import os, time
import requests
import pathlib
from ..modules import valid_uuid
from ..main import AWS_URL, AWS_UPLOAD_URL, APP_AWS_HEALTH_URL, APP_HEALTH_URL, APP_UPLOAD_PDF_URL, APP_UPLOAD_WAV_URL, APP_SCORE_STATUS_URL, APP_MXL_DOWNLOAD_URL, APP_WAV_DOWNLOAD_URL, APP_ANALYZE_PERFORMANCE_URL

load_dotenv()

TEST_MATERIALS_DIR = pathlib.Path(__file__).parent / "test_materials"
TEST_SCORE_PATH = TEST_MATERIALS_DIR / "mozart.pdf"
TEST_WAV_PATH = TEST_MATERIALS_DIR / "test.wav"

def test_analyze_performance():
    """Full integration test which uses /upload, /status, /download and /analyze-performance """ 

    file = {"file": open(TEST_SCORE_PATH, "rb")}
    r = requests.post(APP_UPLOAD_PDF_URL, files=file)
    try:
        r_json = r.json()
        score_id = r_json.get("id", None)
    except Exception as e:
        return {"Error": f"Tried uploading score but received {str(e)}"}, 503

    while True:
        time.sleep(1)
        try:
            request_status = requests.get(APP_SCORE_STATUS_URL, params={"id": score_id})

            assert request_status.status_code == 200, f"Expected success for GET request to {APP_SCORE_STATUS_URL} providing id={score_id} in params, got status code {request_status.status_code}"

            status_json = request_status.json()
            if "status" not in status_json or status_json["status"] != "processing":
                break
        except Exception as e:
            assert False, f"Error encountered when checking status of score id={score_id}: {str(e)}"
    # from here validate that we've completed and try downloading mxl file
    assert "status" in status_json, f"Expected response JSON from status endpoint to contain 'status' key, got keys {status_json.keys()}"
    assert status_json["status"] == "completed", f"Expected status to be 'completed', got {status_json['status']}"  
    
    print("No longer processing, status of pdf to mxl score conversion: ", status_json)

    download_request = requests.get(APP_MXL_DOWNLOAD_URL, params={"id": score_id})

    try:
        content_type = download_request.headers["Content-Type"]
        content_disposition = download_request.headers["Content-Disposition"]

        assert content_type == "application/vnd.recordare.musicxml"

        assert "attachment;" in content_disposition
    except Exception as e:
        assert False, f"Expected to successfully download mxl file for score id {score_id}, but got error {str(e)}"

    try:
        file = {"file": open(TEST_WAV_PATH, "rb")}

        r = requests.post(APP_UPLOAD_WAV_URL, files=file)

        assert r.status_code == 200, f"{r.json()}, {r.status_code} from {APP_UPLOAD_WAV_URL}"

        r_json = r.json()

        id_wav = r_json.get("id")

        analysis_response = requests.post(APP_ANALYZE_PERFORMANCE_URL, json={"id_wav": id_wav, "id_mxl": score_id})

        print(f"Analysis response: {analysis_response.text}")
    except Exception as e:
        assert False, f"Expected to successfully analyze performance using wav id {id_wav} and mxl id {score_id}, but got error {str(e)}"
    