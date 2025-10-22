# warbler-backend

## Setup Instructions
1. Pip install the depedencies:
   ```
   pip install -r requirements.txt
   ```
2. Activate the virtual environment:
   ```
   source .venv/bin/activate
   ```
3. Run the Flask application:
   ```
   flask --app src/api/main.py --debug run
   ```
## Running unit tests
To run the unit tests, use the following command:
```
pytest