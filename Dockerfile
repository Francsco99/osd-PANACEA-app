# Usa Python 3.12 slim come base per ridurre il peso dell'immagine
FROM python:3.12-slim

# Installa pacchetti di base, JDK 17 e dipendenze per PRISM
RUN apt update && apt install -y --no-install-recommends \
    wget \
    tar \
    git \
    openjdk-17-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

# Imposta la cartella di lavoro
WORKDIR /app

# Clona la repository osd-PANACEA-app
RUN git clone https://github.com/Francsco99/osd-PANACEA-app.git /app

# Scarica PRISM in /tmp
RUN wget https://www.prismmodelchecker.org/dl/prism-games-3.2.1-linux64-x86.tar.gz -O /tmp/prism-games.tar.gz

# Estrai PRISM direttamente nella cartella /app/PANACEA
RUN tar -xvf /tmp/prism-games.tar.gz -C /app/PANACEA && rm /tmp/prism-games.tar.gz

# Installa PRISM
RUN cd /app/PANACEA/prism-games-3.2.1-linux64-x86 && ./install.sh

# Corregge i permessi per PRISM
RUN chmod -R u+x /app/PANACEA/prism-games-3.2.1-linux64-x86/bin/*

# Torna nella cartella principale
WORKDIR /app

# Aggiorna pip e installa le dipendenze se il file requirements.txt esiste
RUN pip install --upgrade pip && \
    test -f requirements.txt && pip install --no-cache-dir -r requirements.txt || echo "No requirements.txt found."

# Espone la porta dell'API Flask
EXPOSE 5002 5003

# Comando per avviare entrambi i server in background
CMD ["sh", "-c", "gunicorn --chdir /app/server -b 0.0.0.0:5002 server:app & gunicorn --chdir /app/database -b 0.0.0.0:5003 db:app"]
