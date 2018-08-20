# pull daily files
#
# BUILD-USING:  docker build -t filefetcher .
# RUN-USING:    docker run --detach=true --name filefetcher filefetcher
#

# can't use onbuild due to SSL visibility
FROM python:3.7

RUN apt-get update

# HVO SSL trafic to pypi doesn't go through the SSL inspection devices
# -- tjp 8/20/2018 
#WORKDIR /root/.pip
#ADD support/pip.conf .

WORKDIR /root/certs
add support/DOIRootCA2.cer .

WORKDIR /usr/share/ca-certificates/extra
ADD support/DOIRootCA2.cer DOIRootCA2.crt
RUN echo "extra/DOIRootCA2.crt" >> /etc/ca-certificates.conf && update-ca-certificates

RUN groupadd geology \
  && useradd -g geology geod

ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.1.6/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=c3b78d342e5413ad39092fd3cfc083a85f5e2b75

RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

WORKDIR /app/camfetcher
ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt # 1

ADD VERSION .
ADD camfetcher.py .
ADD update_current_image.py .
ADD support/single.py .
ADD support/cron-camfetcher .
RUN chmod 755 *

CMD ["/usr/local/bin/supercronic","/app/camfetcher/cron-camfetcher"]
