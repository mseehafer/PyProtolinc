""" The remote worker."""

import numpy as np
import numpy.typing as npt
from fastapi import FastAPI

import pyprotolinc.main

app = FastAPI()


@app.get("/")
async def root():
    """ Info sting displaying the version."""
    return {"message": f"Pyprotolinc, version={pyprotolinc.main.__version__}"}


@app.get("/syncrun")
async def syncrun(config_file: str) -> dict[str, list[float]]:
    """ Run job"""

    res: dict[str, npt.NDArray[np.float64]] = pyprotolinc.main.project_cashflows_cli(config_file)
    return {name: list(vec) for name, vec in res.items()}
