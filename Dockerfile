FROM python:3.13-slim

WORKDIR /app

# needed to install Numpy, from docs: https://numpy.org/devdocs/building/
RUN apt-get update
RUN apt install -y gcc g++ gfortran libopenblas-dev liblapack-dev pkg-config python3-pip python3-dev

COPY requirements.txt /app/

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . /app/

RUN useradd warbler
USER warbler

EXPOSE 5000

# healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://127.0.0.1:5000/app-health || exit 1

CMD ["gunicorn", "--workers", "8", "--bind", "0.0.0.0:5000", "src.api.main:app"]