FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

RUN groupadd admin && \
    useradd -g admin admin && \
    chown -R admin:admin /app

USER admin

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]