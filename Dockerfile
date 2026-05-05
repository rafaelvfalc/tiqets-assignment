FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml README.md main.py ./
COPY tiqets_assignment ./tiqets_assignment

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
