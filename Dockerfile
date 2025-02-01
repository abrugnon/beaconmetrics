FROM python:3.10-slim

WORKDIR /app
COPY ./src/ /app/
COPY requirements.txt /app/

RUN pip install -r requirements.txt
STOPSIGNAL SIGINT
EXPOSE 8000

ENTRYPOINT [ "python" ,"-u", "export.py"]