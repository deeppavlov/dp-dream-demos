FROM python:3.7-slim-stretch

EXPOSE 4242

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -y --fix-missing && \
    apt-get install -y -q \
        build-essential \
        openssl \
        git \
        libssl-dev \
        libffi-dev && \
    echo "stty iutf8" >> ~/.bashrc && \
    rm -rf /var/lib/apt/lists/*



COPY requirements.txt /
RUN pip install -r requirements.txt

RUN mkdir deeppavlov-agent
WORKDIR /deeppavlov-agent
COPY . /deeppavlov-agent/.
