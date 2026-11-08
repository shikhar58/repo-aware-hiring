FROM python:3.12-slim
WORKDIR /srv
COPY . .
RUN pip install .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
