# Tunnelchat docker container
#
# VERSION               0.0.2

FROM      ubuntu
MAINTAINER Federico Marani "flagzeta@gmail.com"

# make sure the package repository is up to date
#RUN echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y redis-server python3-pip build-essential python3-dev

ADD . /tunnelchat
RUN pip3 install -r /tunnelchat/requirements.txt 

EXPOSE 8888
WORKDIR /tunnelchat
CMD honcho start
