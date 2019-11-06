FROM ubuntu:18.04

COPY sas2ircu_prom.py /opt/sas2ircu_prom.py

ENTRYPOINT ["/opt/sas2ircu_prom.py"]
