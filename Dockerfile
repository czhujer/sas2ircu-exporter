FROM 2.7-stretch

COPY sas2ircu_prom.py /opt/sas2ircu_prom.py

ENTRYPOINT ["/opt/sas2ircu_prom.py"]
