FROM python:3.12-bookworm

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file principali nel container
COPY . .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta dell'applicazione (modifica se necessario)
EXPOSE 8080

# Comando per avviare l'applicazione
CMD ["python3.12", "src/__main__.py"]
