# Python 3.12
FROM python:3.12-slim as py312
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]"

# Python 3.10
FROM python:3.10-slim as py310
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]"

# Python 3.8
FROM python:3.8-slim as py38
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]"

