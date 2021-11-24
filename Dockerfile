FROM alpine

RUN apk add --no-cache python3 py3-pip

ADD chocoblast-sonar /tmp/chocoblast-sonar
ADD .env .
ADD requirements.txt /tmp
ADD setup.py /tmp

RUN apk add --no-cache build-base python3-dev && \
    pip install --no-cache-dir /tmp && rm -rf /tmp/* && \
    apk --purge del build-base python3-dev

CMD [ "python3", "-m", "chocoblast-sonar" ]