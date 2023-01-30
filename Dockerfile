FROM apache/airflow:2.1.4

USER root
RUN apt-get update && apt-get install -y unzip && apt-get install -y wget && \
    apt-get install libaio1 && mkdir -p /opt/oracle 

RUN sudo mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    sudo wget https://download.oracle.com/otn_software/linux/instantclient/218000/instantclient-basic-linux.x64-21.8.0.0.0dbru.zip && \
    unzip instantclient-basic-linux.x64-21.8.0.0.0dbru.zip && \
    sudo apt-get install libaio1 && \
    sudo sh -c "echo /opt/oracle/instantclient_21_8 > /etc/ld.so.conf.d/oracle-instantclient.conf" && \
    sudo ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_8:$LD_LIBRARY_PATH

ENV AIRFLOW_ENV=dev
ENV AIRFLOW_CONFIG_PAHT=/opt/airflow

USER airflow
COPY requirements.txt requirements.txt
COPY airflow.cfg airflow.cfg
RUN pip install --no-cache-dir --user -r requirements.txt