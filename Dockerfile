FROM --platform=linux/amd64 python:3.8.3

# For nodejs
RUN curl -sL https://deb.nodesource.com/setup_4.x | bash -
RUN apt-get update && apt-get install -y npm netcat nodejs python-dev libmemcached-dev

RUN pip install --upgrade pip  # make things faster, hopefully
COPY codalab/requirements/requirements.txt requirements.txt

RUN pip install --upgrade "pip<24.1"
RUN pip install -r requirements.txt

WORKDIR /app/codalab
