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

def test_pytest():
    assert 4 == 4

def test_connection():
    """Simple integration test: ensure Flask backend responds at health check URL."""

    r = requests.get(APP_HEALTH_URL, timeout=3)

    assert r.status_code == 200, f"Expected 200 from {APP_HEALTH_URL}, got {r.status_code}"

def test_aws_connection():
    """Simple integration test: ensure AWS Audiveris backend responds at health check URL."""

    r = requests.get(AWS_URL)
    assert r.status_code == 200, f"Expected status code 200 for GET request to {AWS_URL}, got {r.status_code}"

def test_audiveris_post_error():
    """simple integration test: ensure Audiveris doesn't allow non-post requests to /upload"""
    r = requests.get(AWS_UPLOAD_URL)
    assert r.status_code != 200, f"Expected failure for GET request to {AWS_UPLOAD_URL}, got {r.status_code}"

def test_aws_health_check():
    """Integration test whether the AWS hosted endpiont is available"""
    r = requests.get(APP_AWS_HEALTH_URL)
    assert r.status_code == 200, f"Expected 200 status code for GET request to {APP_AWS_HEALTH_URL}, got {r.status_code}"


def test_audiveris_post_correct():
    """Simple integration test: ensure deployed AWS container accepts valid POST requests to /upload and returns a uuid """
    
    file = {"file": open(TEST_SCORE_PATH, "rb")}

    r = requests.post(AWS_UPLOAD_URL, files=file)

    assert r.status_code == 200, f"Expected success for POST request of uploading {TEST_SCORE_PATH} to {AWS_UPLOAD_URL}, got status code {r.status_code}"

    r_json = r.json()

    assert "id" in r_json.keys(), f"Expected response JSON to contain 'id' key, the keys are actually just {r_json.keys()}"

    assert valid_uuid(r_json["id"]), f"Expected response value for key 'id' to be a valid UUID, got {r_json['id']} which is not valid uuid according to valid_uuid() function"

def test_upload_score_and_check_status_integration():
    """Integration test for the upload_score and status function in src/api/main.py"""

    file = {"file": open(TEST_SCORE_PATH, "rb")}

    r = requests.post(APP_UPLOAD_PDF_URL, files=file)

    assert r.status_code == 200, f"Expected success for POST request of uploading {TEST_SCORE_PATH} to {APP_UPLOAD_PDF_URL}, got status code {r.status_code}"

    r_json = r.json()
    score_id = r_json.get("id", None)

    assert "id" in r_json.keys(), f"Expected response JSON to contain 'id' key, the keys are actually just {r_json.keys()}"

    assert valid_uuid(score_id), f"Expected response value for key 'id' to be a valid UUID, got {score_id} which is not valid uuid according to valid_uuid() function"

    r2 = requests.get(APP_SCORE_STATUS_URL, params={"id": score_id})

    assert r2.status_code == 200, f"Expected success for GET request to {APP_SCORE_STATUS_URL} providing id={score_id} in params, got status code {r2.status_code}"

def test_upload_wav_endpoint():
    """Integration test for the /upload/wav endpoint in src/api/main.py"""

    file = {"file": open(TEST_WAV_PATH, "rb")}

    r = requests.post(APP_UPLOAD_WAV_URL, files=file)

    assert r.status_code == 200, f"{r.json()}, {r.status_code} from {APP_UPLOAD_WAV_URL}"

    r_json = r.json()

    assert "id" in r_json.keys(), f"Expected response JSON to contain 'id' key, the keys are actually just {r_json.keys()}"

def test_download_wav_endpoint():
    """Integration test for the /download/wav endpoint in src/api/main.py"""

    # first upload a wav file
    file = {"file": open(TEST_WAV_PATH, "rb")}

    r = requests.post(APP_UPLOAD_WAV_URL, files=file)

    assert r.status_code == 200, f"{r.json()}, {r.status_code} from {APP_UPLOAD_WAV_URL}"

    r_json = r.json()

    assert "id" in r_json.keys(), f"Expected response JSON to contain 'id' key, the keys are actually just {r_json.keys()}"

    wav_id = r_json["id"]

    # now try downloading the wav file
    download_request = requests.get(APP_WAV_DOWNLOAD_URL, params={"id": wav_id})

    try:
        content_type = download_request.headers["Content-Type"]
        content_disposition = download_request.headers["Content-Disposition"]

        assert content_type == "audio/wav"

        assert "attachment;" in content_disposition
    except Exception as e:
        assert False, f"Expected to successfully download wav file for wav id {wav_id}, but got error {str(e)}"