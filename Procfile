web: uvicorn api:app --host 0.0.0.0 --port $PORT
worker: python -c "from scheduler.scheduler import iniciar_scheduler; iniciar_scheduler()"
