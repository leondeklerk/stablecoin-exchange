FROM python:3.7.7-alpine

ENV PATH="/scripts:${PATH}"

RUN apk add --update --no-cache libsodium libressl
RUN apk add --update --no-cache --virtual .tmp python3-dev build-base linux-headers libffi-dev libressl-dev musl-dev cargo

RUN pip install cryptography #cache install to avoid building each time requirements change

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN apk del .tmp

RUN adduser -D user

RUN mkdir /eurotoken
COPY ./stablecoin /eurotoken
WORKDIR /eurotoken
RUN chmod -R 755 /eurotoken

USER user

CMD ["python", "-u", "run_coin.py"]
