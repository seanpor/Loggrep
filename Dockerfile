# Python 3.14
FROM python:3.14-slim as py314
WORKDIR /app
# Create non-root user for security and proper permission testing
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" && \
    chown -R appuser:appuser /app
USER appuser

# Python 3.13
FROM python:3.13-slim as py313
WORKDIR /app
# Create non-root user for security and proper permission testing
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" && \
    chown -R appuser:appuser /app
USER appuser

# Python 3.12
FROM python:3.12-slim as py312
WORKDIR /app
# Create non-root user for security and proper permission testing
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" && \
    chown -R appuser:appuser /app
USER appuser

# Python 3.11
FROM python:3.11-slim as py311
WORKDIR /app
# Create non-root user for security and proper permission testing
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" && \
    chown -R appuser:appuser /app
USER appuser

# Python 3.10
FROM python:3.10-slim as py310
WORKDIR /app
# Create non-root user for security and proper permission testing
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" && \
    chown -R appuser:appuser /app
USER appuser

# Python 3.9
FROM python:3.9-slim as py39
WORKDIR /app
# Create non-root user for security and proper permission testing
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" && \
    chown -R appuser:appuser /app
USER appuser

# Python 3.8
FROM python:3.8-slim as py38
WORKDIR /app
# Create non-root user for security and proper permission testing
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" && \
    chown -R appuser:appuser /app
USER appuser

# Python 3.7 (minimal support)
FROM python:3.7-slim as py37
WORKDIR /app
# Create non-root user for security and proper permission testing
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" && \
    chown -R appuser:appuser /app
USER appuser

