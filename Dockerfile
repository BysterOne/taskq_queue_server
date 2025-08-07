FROM python:3.12-slim

WORKDIR /srv/app
ENV PATH=/srv/app-venv/bin:$PATH

ARG DEBIAN_FRONTEND=noninteractive

ARG BUILD_DEPS="\
    file \
    gcc \
    libc6-dev \
    libffi-dev \
    libpq-dev \
    make \
    git \
"

ARG RUNTIME_DEPS="\
    libpq5 \
    gdal-bin \
"

# install dependencies
COPY requirements.txt /srv/app

RUN apt-get -qq update \
    && apt-get -qqy --no-install-recommends install \
        $BUILD_DEPS \
        $RUNTIME_DEPS \
    && python3 -m venv /srv/app-venv \
    && pip --no-cache-dir install \
        -r requirements.txt \
    && apt-get -y purge $BUILD_DEPS \
    && apt-get -y autoremove \
    && rm -rf /var/lib/apt/lists/*

COPY ./app /srv/app/
