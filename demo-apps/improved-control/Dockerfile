# Static fixture only: this recipe has not been built or deployed.
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')"
CMD ["flask", "--app", "app", "run", "--host", "0.0.0.0"]
