FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /scribe-service

COPY ./requirements.txt /scribe-service/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /scribe-service/requirements.txt

COPY ./app /scribe-service/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]