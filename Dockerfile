FROM ubuntu:18.04

RUN apt-get update && apt-get install python -y

COPY utils/sas2ircu /usr/local/bin/sas2ircu

COPY sas2ircu_prom.py /opt/sas2ircu_prom.py

CMD ["/opt/sas2ircu_prom.py"]
