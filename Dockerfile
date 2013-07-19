# Tunnelchat docker container
#
# VERSION               0.0.1

FROM      ubuntu
MAINTAINER Federico Marani "flagzeta@gmail.com"

# make sure the package repository is up to date
RUN echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
RUN apt-get update

RUN apt-get install -y redis-server python-virtualenv python-pip

ADD . /tunnelchat
RUN virtualenv /tunnelchat_env && /tunnelchat_env/bin/pip install -r /tunnelchat/requirements.txt 
RUN chmod a+x /tunnelchat/start.sh

EXPOSE 8888

CMD /tunnelchat/start.sh
