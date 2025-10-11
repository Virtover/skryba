FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /api-gateway

COPY ./requirements.txt /api-gateway/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /api-gateway/requirements.txt

COPY ./app /api-gateway/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
