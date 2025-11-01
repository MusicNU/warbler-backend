FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . /app/

RUN useradd warbler
USER warbler

EXPOSE 5000

# healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD curl -f http://127.0.0.1:5000/app-health || exit 1

CMD ["gunicorn", "--workers", "8", "--bind", "0.0.0.0:5000", "src.api.main:app"]