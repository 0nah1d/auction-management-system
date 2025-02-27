FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY . /app/

COPY entrypoint.sh /

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["sh", "./entrypoint.sh"]