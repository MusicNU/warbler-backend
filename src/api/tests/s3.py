import os
import pathlib
import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(pathlib.Path(__file__).parent.parent.parent.parent / ".env")

os.environ['AWS_SHARED_CREDENTIALS_FILE'] = str(pathlib.Path(__file__).parent.parent.parent.parent / ".aws" / "credentials")

AWS_PROFILE_NAME = str(os.getenv("AWS_PROFILE_NAME", "AWS profile name does not exist"))

assert AWS_PROFILE_NAME == '089276191632_sesp-rch-worsley-musicnu_admin', f"wrong AWS_PROFILE_NAME: {AWS_PROFILE_NAME}"

session = boto3.Session(profile_name='089276191632_sesp-rch-worsley-musicnu_admin')
s3 = session.client('s3')

s3.upload_file('README.md', 'musicnu', '2.md')