FROM python:3.6.2-jessie
RUN mkdir -p /opt/work

WORKDIR "/opt/work"
VOLUME ["/opt/work"]
