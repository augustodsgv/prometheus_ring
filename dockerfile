FROM python:3

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 9988

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "9988", "--log-level", "debug", "prometheus_ring.main:app"]