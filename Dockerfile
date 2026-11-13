# NÃO TESTADO: o ambiente de desenvolvimento não tinha Docker. Revise antes de usar.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY promptshield ./promptshield
COPY data ./data
COPY legacy-sprint1/data ./legacy-sprint1/data
# O modelo é treinado no build (TF-IDF + LogReg treina em segundos, em CPU).
RUN python -m promptshield.train
ENV PROMPTSHIELD_MODEL_PATH=/app/artifacts/model.joblib
EXPOSE 8000
CMD ["uvicorn", "promptshield.api:app", "--host", "0.0.0.0", "--port", "8000"]
