ARG PYTHON_IMAGE_BASE=python:3.12-slim

FROM $PYTHON_IMAGE_BASE

ARG BUILD_DEPS="\
    file \
    gcc \
    libc6-dev \
    libffi-dev \
    libpq-dev \
    make \
"

ARG RUNTIME_DEPS="\
    libpq5 \
    gdal-bin \
    libzbar0 \
    nano \
"

WORKDIR /srv/app

ENV PATH=/srv/app-venv/bin:$PATH
ENV DEBIAN_FRONTEND=noninteractive
ENV TIKTOKEN_CACHE_DIR=/srv/app/cache
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=UTF-8
ENV LOG_FORMATTER=json

COPY app/pyproject.toml app/poetry.lock ./

RUN apt-get update \
    && apt-get -y --no-install-recommends install \
        $BUILD_DEPS \
        $RUNTIME_DEPS \
    && pip install --upgrade pip wheel cython coverage poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root --no-directory --no-cache \
    && apt-get -y purge $BUILD_DEPS \
    && apt-get -y autoremove \
    && rm -rf /var/lib/apt/lists/*

COPY app /srv/app

RUN poetry install --only main --no-directory
