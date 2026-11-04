# Recuerde poner aquí los datos de conexión y guardar como secret_config.py

# ==========================================
# CONFIGURACIÓN DE BASE DE DATOS POSTGRESQL
# ==========================================

PGHOST = os.getenv("PGHOST", "PONGA EL HOST DE LA BD AQUI")
PGDATABASE = os.getenv("PGDATABASE", "PONGA EL NOMBRE DE LA BD AQUI")
PGUSER = os.getenv("PGUSER", "PONGA EL USUARIO AQUI")
PGPASSWORD = os.getenv("PGPASSWORD", "PONGA LA CONTRASEÑA AQUI")
PGPORT = int(os.getenv("PGPORT", "5432"))

# ==========================================
# CONFIGURACIÓN DE INTELIGENCIA ARTIFICIAL
# ==========================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "PONGA SU KEY DE GROQ AQUI")