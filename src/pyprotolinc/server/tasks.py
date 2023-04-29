"""
Start a celery worker:

celery -A pyprotolinc.server.tasks worker --loglevel=INFO

"""

import numpy as np
import numpy.typing as npt
from celery import Celery

import pyprotolinc.main


app = Celery('tasks', backend='rpc://', broker='redis://localhost')


@app.task
def add(x, y):
    return x + y


@app.task
def valuation_run(config_file: str) -> dict[str, list[float]]:  # dict[str, npt.NDArray[np.float64]]:   # dict[str, list[float]]:
    # res: dict[str, npt.NDArray[np.float64]] = pyprotolinc.main.project_cashflows_cli(config_file)
    # return {name: list(vec) for name, vec in res.items()}
    res = pyprotolinc.main.project_cashflows_cli(config_file)
    return {name: list(vec) for name, vec in res.items()}