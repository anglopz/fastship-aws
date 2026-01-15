FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /code

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto (incluyendo el paquete app)
COPY . /code

# Asegurar que el paquete raíz `app` sea importable (para `app.main`)
ENV PYTHONPATH=/code

# Arrancar la aplicación FastAPI
# Render uses dynamic PORT environment variable
# Use shell form to allow environment variable substitution
# Note: EXPOSE doesn't support variables, but Render will detect the port from CMD
CMD sh -c "echo 'Starting on port ${PORT:-8000}' && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
