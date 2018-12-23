FROM python:3.6.2-jessie

ADD requirements.txt .
RUN pip install -r requirements.txt
RUN mkdir -p /opt/work

WORKDIR "/opt/work"
VOLUME ["/opt/work"]
