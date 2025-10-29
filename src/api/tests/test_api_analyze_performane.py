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
    r = requests.post(APP_ANALYZE_PERFORMANCE_URL, json={"id_wav": "19e236b5-e5ce-4f6e-84f8-fb779392120a", "id_mxl": "23ac9da4-3db9-4ce5-b9b5-4fb749afcb06"})

    print(r.text)

    assert r.status_code == 200, f"Expected 200 status code, got {r.status_code}"

