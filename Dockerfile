FROM python:3.6.2-jessie

RUN pip install jinja2
RUN mkdir -p /opt/work

WORKDIR "/opt/work"
VOLUME ["/opt/work"]
