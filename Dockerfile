FROM alpine

RUN apk add --no-cache python3 py3-pip

ADD chocoblast-sonar /tmp/chocoblast-sonar
ADD requirements.txt /tmp
ADD setup.py /tmp

RUN apk add --no-cache build-base python3-dev && \
    pip install --no-cache-dir /tmp && rm -rf /tmp/* && \
    find /usr/lib -name "*.pyc" -delete && \
    find /usr/lib -name "__pycache__" -delete && \
    apk --purge del build-base python3-dev

CMD [ "python3", "-um", "chocoblast-sonar" ]