from ubuntu:18.04
ENV DEBIAN_FRONTEND=noninteractive

#install prerequisites
RUN apt-get -q update && \
    apt-get -q -y install python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/ /var/cache/apt/ /var/cache/debconf/

ADD monitor-queue.py requirements.txt /opt/

RUN pip3 install -r /opt/requirements.txt

CMD "/opt/monitor-queue.py"
