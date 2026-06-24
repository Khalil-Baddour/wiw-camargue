FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Le catalogue est monté en volume à /catalogue à l'exécution.
# CATALOG_DIR dans main.py remonte de 3 niveaux depuis /app/app/main.py → /catalogue.

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
