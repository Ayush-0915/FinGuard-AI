# MuleGuard backend API only. The PySide6 desktop UI runs on the analyst's computer.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MULEGUARD_REPORTS_DIR=/var/lib/muleguard/reports

WORKDIR /app

# LightGBM requires the OpenMP runtime at execution time.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
# The repository requirements also include the desktop UI and notebook tools.
# They are intentionally excluded from the server image.
RUN sed -E '/^(matplotlib|seaborn|jupyter|pyside6)(==.*)?$/d' requirements.txt > requirements.api.txt \
    && pip install --upgrade pip \
    && pip install -r requirements.api.txt

COPY backend ./backend
COPY models ./models

RUN useradd --create-home --uid 10001 muleguard \
    && mkdir -p /var/lib/muleguard/reports \
    && chown -R muleguard:muleguard /app /var/lib/muleguard

USER muleguard

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
