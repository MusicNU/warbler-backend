# warbler-backend
Backend API endpoints and processing algorithms for Warbler. 

## Requirements
- Python 3.10+
- An .env file with the following variables:
  - `API_URL`: where the backend API is hosted, default is local at `http://127.0.0.1:5000`
  - `AUDIVERIS_API_URL`: AWS url for Audiveris wrapper container 

## Setup Instructions
1. Set up your `.env` file with the required environment variables.
2. Pip install the depedencies:
   ```
   pip install -r requirements.txt
   ```
3. Activate the virtual environment:
   ```
   source .venv/bin/activate
   ```
4. Run the Flask application:
   ```
   flask --app src/api/main.py --debug run
   ```

## Running unit tests
To run the unit tests, use the following command:
```
pytest