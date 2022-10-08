FROM ghcr.io/maxotta/kiv-ds-docker:latest

RUN yum -q -y install python3

COPY . /opt/view

RUN pip3 install -r /opt/view/python/requirements.txt

#CMD /usr/bin/python3 /opt/view/python/main.py