"""Plantilla segura: copia como secret_config.py o configura estas variables en el entorno."""
import os

PGHOST = os.getenv("PGHOST", "")
PGDATABASE = os.getenv("PGDATABASE", "")
PGUSER = os.getenv("PGUSER", "")
PGPASSWORD = os.getenv("PGPASSWORD", "")
PGPORT = int(os.getenv("PGPORT", "5432"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
