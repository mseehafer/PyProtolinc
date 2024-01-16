""" The remote worker.

     uvicorn pyprotolinc.server.api:app --reload

     Input for  API test: /mnt/c/Programming/python/PyProtolinc/examples/03_mortality/config_for_cli_runner.yml
"""

import os
import tempfile
from typing import Union
from datetime import datetime, timezone
import pytz
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import pandas as pd

import pyprotolinc.main
# from pyprotolinc.server.tasks import valuation_run
from pyprotolinc.server.celery_client import run_distributed_job, run_distributed_job_test
from pyprotolinc.server.tasks import jobs as jobs_col
from pyprotolinc.server.tasks import results as results_col

app = FastAPI()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")


# notes:
# https://stackoverflow.com/questions/13271056/how-to-chain-a-celery-task-that-returns-a-list-into-a-group


@app.get("/", response_class=HTMLResponse)
async def read_items():
    return """
    <html>
        <head>
            <title>PyProtolinc Event Interface</title>
        </head>
        <body>
            <h1>PyProtolinc API Event Interface</h1>

            <p> Simple web client that allows to access PyProtolinc API: <a href="docs">DEV-API</a>
            </p>
        </body>
    </html>
    """


@app.get("/info")
async def info():
    """ Info sting displaying the version."""
    return {"message": f"Pyprotolinc, version={pyprotolinc.main.__version__}"}


@app.post("/test")
async def jobrun_test(config_file: str) -> str:  # dict[str, list[float]]:
    """ Run job. """

    # validate the params

    # generate new job id
    job_id = str(uuid.uuid1())
    print("API: new job id", job_id)
    jobs_col.insert_one({"_id": job_id,
                         "params": {"config_file": config_file},
                         "events": [{'type': "API_JOB_RECEIVED",
                                     'state': "TO_BE_SUBMITTED",
                                     "timestamp": datetime.now(tz=timezone.utc).timestamp()}],
                         "subtasks": {}
                         })

    main_task_id = run_distributed_job_test(job_id, config_file)

    # print(res)
    return job_id


@app.post("/jobs/run")
async def jobrun(config_file: str) -> str:  # dict[str, list[float]]:
    """ Run job"""

    # res: dict[str, npt.NDArray[np.float64]] = pyprotolinc.main.project_cashflows_cli(config_file)
    res_id = run_distributed_job(config_file)

    jobs_col.insert_one({"_id": res_id,
                         "params": {"config_file": config_file},
                         "events": [{'type': "API_JOB_RECEIVED",
                                     'state': "TO_BE_SUBMITTED",
                                     "timestamp": datetime.now(tz=timezone.utc).timestamp()}],
                         "subtasks": []
                         })

    # return {name: list(vec) for name, vec in res.items()}
    return res_id


SubDictType = dict[str, Union[float, str, int]]

@app.get("/jobs")
async def job_status() -> list[dict[str, Union[float, str, int, list[SubDictType]]]]:
    """ Retrieve status information fro each job. """

    # query to collect the latest event
    # q = jobs_col.aggregate([{"$project": {"latestEvent": {"$last": "$events"}, "firstEvent": {"$first": "$events"}}},
    #                         {"$project": {"_id": 0,
    #                                       "job_id": "$_id",
    #                                       "submitted_at": "$firstEvent.timestamp",
    #                                       "state": "$latestEvent.state",
    #                                       "timestamp": "$latestEvent.timestamp"}},
    #                         {"$sort": {"submitted_at": 1}},
    #                         ])

    # TODO: filter for time!
    q = jobs_col.aggregate([{"$match": {"events.0.timestamp": {"$gte": 1683376773.800887}}},  # filter for started date
                            {"$project": {"_id": True, "job_started": {"$first": "$events"}, "subtasks": True}},
                            {'$addFields': {'subtasksarr': {"$objectToArray": '$subtasks'}}},
                            {'$project': {'subtasks_new': '$subtasksarr.v', "job_started": "$job_started.timestamp"}},
                            {'$project': {'subtasks': False, 'subtaskarr': False}},
                            {'$unwind': '$subtasks_new'},
                            {"$project": {"_id": True,
                                          'name': "$subtasks_new.name",
                                          "task_id": "$subtasks_new.task_id",
                                          "job_started": True,
                                          "firstEvent": {"$first": "$subtasks_new.events"},
                                          "latestEvent": {"$last": "$subtasks_new.events"}}},
                            {'$project': {"_id": True, "name": True, "task_id": True, "job_started": True,
                                          "started": "$firstEvent.timestamp",
                                          "latest_update": "$latestEvent.timestamp",
                                          "status": "$latestEvent.state"
                                        }},
                            {'$sort': {"_id": 1, "started": 1}},
                            {"$group": {"_id": "$_id", "job_started": {"$max": "$job_started"},
                                        "subtasks": {"$push": {"task_id": "$task_id",
                                                               "name": "$name",
                                                               "status": "$status",
                                                               "started": "$started",
                                                               "latest_update": "$latest_update"}}}},
                            {"$sort": {"job_started": 1}}
                            ])

    task_status = []
    for job_info in list(q):
        _convert_timestamps_in_dict(job_info, alt_keys=["job_started"])
        _convert_timestamps_in_list(job_info["subtasks"], ["started", "latest_update"])
        task_status.append(job_info)

    print(task_status)

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


def _convert_timestamps_in_list(inp: list[dict[str, Union[str, int, float, None]]], alt_keys: list[str] = []) -> None:
    """ Modifies all object in the list passed in replacing all 'timestamp' values under a key
    of the same name with a string representation of the timestamp. """

    for q in inp:
        _convert_timestamps_in_dict(q, alt_keys)
