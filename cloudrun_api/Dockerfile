FROM python:3.10-slim

WORKDIR /app
COPY app.py .

RUN pip install flask

ENV FLAG="TFM{CLOUD_RUN_OIDC_ESCALATION}"
ENV SECRET_KEY="super-secret-api-key-98431"

CMD ["python", "app.py"]
