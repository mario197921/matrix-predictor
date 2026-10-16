FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
# CORS/XSRF disattivati: dietro Firebase Hosting l'Origin (matrix.mtapp.it) non
# coincide con l'Host interno di Cloud Run e Streamlit rifiuterebbe il WebSocket.
CMD streamlit run app.py \
    --server.port=$PORT --server.address=0.0.0.0 --server.headless=true \
    --server.enableCORS=false --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
