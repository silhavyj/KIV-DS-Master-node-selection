FROM ghcr.io/maxotta/kiv-ds-docker:latest

RUN yum -q -y install python3

COPY . /opt/app

RUN pip3 install -r /opt/app/requirements.txt

# CMD /usr/bin/python3 /opt/app/main.py