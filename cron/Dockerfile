FROM ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y tzdata language-pack-ja
ENV TZ=Asia/Tokyo
ENV LANG=$LANG=:ja_JP.UTF-8
RUN LC_ALL=ja_JP.UTF-8


RUN apt-get install -y busybox-static python3 python3-dev python3-pip libpq-dev vim

# for wattstats
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# setup cron
COPY src /usr/local/bin
RUN chmod -R 744 /usr/local/bin

COPY crontabs/jobs ./
# RUN busybox crontab jobs
COPY crontabs/jobs /var/spool/cron/crontabs/root
CMD ["busybox", "crond", "-f"]
