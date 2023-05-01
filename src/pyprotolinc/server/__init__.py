"""

   To make this work one needs to:

    - start redis
    - start mongodb
    - start a celery worker (celery -A pyprotolinc.server.tasks worker --loglevel=INFO)
    - start the celery event monitor (python src/pyprotolinc/server/tasks.py)
    - start the API server (uvicorn pyprotolinc.server.api:app --reload)

    Start a mongo shell:
    docker exec -it mongodb2 bash
    then mongosh




"""
