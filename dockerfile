FROM python:3.14-alpine

WORKDIR /app

COPY . .

RUN pip install flask

EXPOSE 5000

CMD ["python3", "server.py"]