# FROM ubuntu:18.04
FROM python:3.7.7-slim-stretch
ENV LANG C.UTF-8
ENV DEV="gcc wget gnupg"

RUN DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y $DEV && \
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main" > /etc/apt/sources.list.d/postgresql.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get install -y tzdata busybox-static postgresql-client-12 libpq-dev
ENV TZ=Asia/Tokyo
# ENV LANG=$LANG:ja_JP.UTF-8
# ENV LC_ALL=ja_JP.UTF-8

    # apt-get install -y tzdata language-pack-ja busybox-static libpq-dev && \
# RUN apt-get install -y busybox-static python3 python3-pip libpq-dev vim

# for wattstats
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# setup cron
COPY src /usr/local/bin
RUN chmod -R 744 /usr/local/bin

COPY crontabs/jobs /var/spool/cron/crontabs/root

RUN apt-get -y remove $DEV && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

CMD ["busybox", "crond", "-f"]
