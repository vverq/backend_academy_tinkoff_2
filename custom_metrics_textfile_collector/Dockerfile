FROM ubuntu:latest

RUN apt update
RUN apt install python3 -y

COPY log_size_bytes.py /opt/log_size_bytes.py

CMD [ "python3", "/opt/log_size_bytes.py" ]