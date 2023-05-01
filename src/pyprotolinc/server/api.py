""" The remote worker.

     uvicorn pyprotolinc.server.api:app --reload

     Input for  API test: /mnt/c/Programming/python/PyProtolinc/examples/03_mortality/config_for_cli_runner.yml
"""

import os
import tempfile
from typing import Union
from datetime import datetime, timezone
import pytz

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import pandas as pd

import pyprotolinc.main
# from pyprotolinc.server.tasks import valuation_run
from pyprotolinc.server.celery_client import run_distributed_job
from pyprotolinc.server.tasks import jobs as jobs_col
from pyprotolinc.server.tasks import results as results_col

app = FastAPI()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")


@app.get("/info")
async def info():
    """ Info sting displaying the version."""
    return {"message": f"Pyprotolinc, version={pyprotolinc.main.__version__}"}


@app.get("/syncrun")
async def syncrun(config_file: str) -> str:  # dict[str, list[float]]:
    """ Run job"""

    # res: dict[str, npt.NDArray[np.float64]] = pyprotolinc.main.project_cashflows_cli(config_file)
    res_id = run_distributed_job(config_file)

    jobs_col.insert_one({"_id": res_id,
                         "params": {"config_file": config_file},
                         "events": [{'type': "API_JOB_RECEIVED",
                                     'state': "TO_BE_SUBMITTED",
                                     "timestamp": datetime.now(tz=timezone.utc).timestamp()}]})

    # return {name: list(vec) for name, vec in res.items()}
    return res_id


@app.get("/jobs")
async def job_status() -> list[dict[str, Union[float, str, int]]]:
    """ Retrieve status information fro each job. """

    # query to collect the latest event
    q = jobs_col.aggregate([{"$project": {"latestEvent": {"$last": "$events"}, "firstEvent": {"$first": "$events"}}},
                            {"$project": {"_id": 0,
                                          "job_id": "$_id",
                                          "submitted_at": "$firstEvent.timestamp",
                                          "state": "$latestEvent.state",
                                          "timestamp": "$latestEvent.timestamp"}},
                            {"$sort": {"submitted_at": 1}},
                            ])

    task_status = []
    for job_info in list(q):
        _convert_timestamps_in_dict(job_info, alt_keys=["submitted_at"])
        task_status.append(job_info)

    return task_status


@app.get("/jobs/{job_id}/events")
async def job_events(job_id: str) -> list[dict[str, Union[str, int, float, None]]]:  # dict[str, list[float]]:
    """ Retrieve status information for a specified job. """

    jobs = list(jobs_col.find({"_id": job_id}))

    if len(jobs) == 1:
        # convert all timestamps
        _convert_timestamps_in_list(jobs[0]["events"])
        return jobs[0]["events"]
    else:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/jobs/{job_id}/results")
async def job_result(job_id: str) -> dict[str, list[float, int]]:
    """ Retrieve results from a specified job. """

    result = list(results_col.find({"_id": job_id}))

    if len(result) == 1:
        return result[0]["data"]
    else:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/jobs/{job_id}/results/csv")
async def job_result_csv(job_id: str) -> dict[str, list[float, int]]:
    """ Retrieve results from a specified job. """

    filename = f"pyprotolinc_result_{job_id}.csv"
    path = os.path.join(DOWNLOADS_DIR, filename)

    if not os.path.exists(path):
        print("Creating download file...")
        result = list(results_col.find({"_id": job_id}))
        if len(result) != 1:
            raise HTTPException(status_code=404, detail="Item not found")
        res_data = result[0]["data"]
        pd.DataFrame(res_data).to_csv(path)

    return FileResponse(path=path, filename=filename, media_type='text/csv')


@app.get("/jobs/{job_id}/results/excel")
async def job_result_excel(job_id: str) -> dict[str, list[float, int]]:
    """ Retrieve results from a specified job. """

    filename = f"pyprotolinc_result_{job_id}.xlsx"
    path = os.path.join(DOWNLOADS_DIR, filename)

    if not os.path.exists(path):
        print("Creating download file...")
        result = list(results_col.find({"_id": job_id}))
        if len(result) != 1:
            raise HTTPException(status_code=404, detail="Item not found")
        res_data = result[0]["data"]

        pd.DataFrame(res_data).to_excel(path)

    return FileResponse(path=path, filename=filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


def _convert_timestamps_in_dict(o: dict[str, Union[str, int, float, None]], alt_keys: list[str] = []) -> None:
    """ Modifies the object passed in replacing all 'timestamp' values under a key
    of the same name with a string representation of the timestamp. """

    for key in set(["timestamp"] + alt_keys):
        ts = o.get(key)
        if ts is not None:
            ts_dt = datetime.fromtimestamp(ts, pytz.utc)
            o[key] = ts_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        # ts.astimezone(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d %H:%M:%S %Z%z')


def _convert_timestamps_in_list(inp: list[dict[str, Union[str, int, float, None]]]) -> None:
    """ Modifies all object in the list passed in replacing all 'timestamp' values under a key
    of the same name with a string representation of the timestamp. """

    for q in inp:
        _convert_timestamps_in_dict(q)
