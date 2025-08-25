FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements (del directorio raíz)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del scheduler
COPY scheduler/ ./scheduler/
COPY api/ ./api/

# Crear usuario no-root
RUN groupadd -r scheduler && useradd -r -g scheduler scheduler
RUN chown -R scheduler:scheduler /app
USER scheduler

# Comando por defecto
CMD ["python", "scheduler/main.py"]
