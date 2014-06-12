# Tunnelchat docker container
#
# VERSION               0.0.2

FROM      ubuntu
MAINTAINER Federico Marani "flagzeta@gmail.com"

# make sure the package repository is up to date
RUN apt-get update
RUN apt-get install -y redis-server python3-pip build-essential python3-dev
RUN apt-get install -y wget unzip
RUN apt-get install -y ruby

# install dart sdk
WORKDIR /tmp
RUN wget http://storage.googleapis.com/dart-archive/channels/stable/release/latest/sdk/dartsdk-linux-x64-release.zip
RUN unzip dartsdk-linux-x64-release.zip
RUN mv dart-sdk /opt
ENV PATH /opt/dart-sdk/bin:$PATH

# install compass
RUN gem install bootstrap-sass compass

# install python dependencies
ADD . /tunnelchat
RUN pip3 install -r /tunnelchat/requirements.txt 

# compile dart/sass
WORKDIR /tunnelchat/static
RUN pub get
RUN make clean all

EXPOSE 8888
WORKDIR /tunnelchat
CMD honcho start
