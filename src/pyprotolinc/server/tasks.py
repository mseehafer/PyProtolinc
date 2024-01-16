"""
Start a celery worker:

celery -A pyprotolinc.server.tasks worker --loglevel=INFO

"""

from typing import Any
import time
import ast

from celery import Celery, group, chain
from celery import chord
import pymongo
import pymongo.database
import pymongo.collection
import pyprotolinc.main


#app = Celery('tasks', backend='rpc://', broker='redis://localhost')
app = Celery('tasks', backend='redis://localhost', broker='redis://localhost')
# app = Celery('tasks', broker='redis://localhost')
app.conf.update(
    worker_send_task_events=True    # needed for monitoring
)

# mongo db instance
client: pymongo.MongoClient = pymongo.MongoClient("localhost", 27017)
db: pymongo.database.Database = client.pyprotolinc
jobs: pymongo.collection.Collection = db.jobs
results: pymongo.collection.Collection = db.results


# @app.task
# def add(x, y):
#     return x + y

# 
# NOTE: It is assumed that the the job_id is always passed in as key-word arg
#       This ensures it can be identified in the monitoring


@app.task(bind=True)
def valuation_run(self, config_file: str) -> dict[str, list[float]]:  # dict[str, npt.NDArray[np.float64]]:   # dict[str, list[float]]:
    """ Valuation run as a remote task. """
    # res: dict[str, npt.NDArray[np.float64]] = pyprotolinc.main.project_cashflows_cli(config_file)
    # return {name: list(vec) for name, vec in res.items()}

    task_id = self.request.id  # task ID from celery

    # calculate and make result serializable
    res = pyprotolinc.main.project_cashflows_cli(config_file)
    res_serializable = {name: [float(v) for v in vec] for name, vec in res.items()}

    # store result in DB
    results.insert_one({"_id": task_id, "data": res_serializable})
    # return res_serializable


@app.task(bind=True)
def valuation_run_modular(self, config_file: str, job_id: str) -> int:
    """ Valuation run as a remote task. """
    # res: dict[str, npt.NDArray[np.float64]] = pyprotolinc.main.project_cashflows_cli(config_file)
    # return {name: list(vec) for name, vec in res.items()}

    task_id = self.request.id  # task ID from celery

    # load portfolio
    portfolio = list(range(1, 101))

    # split portfolio
    sub_portfolios = []
    count = 0
    for p in portfolio:
        count += 1
        if count > 20:
            count = 1
        if count == 1:
            sub_ptf = []
            sub_portfolios.append(sub_ptf)
        sub_ptf.append(p)

    # trigger subtasks
    subtasks = chord(valuation_subportfolio.s(sub_ptf, config_file, job_id=job_id) for sub_ptf in sub_portfolios)(combine_subportflio_results.s(job_id=job_id))
    return task_id
    # # store result in DB
    # results.insert_one({"_id": task_id, "data": res_serializable})
    # # return res_serializable


# @app.task(bind=True)
# def load_and_splitportfolio(self, config_file: str) -> list[list[(int, str)]]:   # dict[str, list[float]]:
#     # load portfolio
#     portfolio = list(range(1, 101))

#     # split portfolio
#     sub_portfolios = []
#     count = 0
#     for p in portfolio:
#         count += 1
#         if count > 10:
#             count = 1
#         if count == 1:
#             sub_ptf = []
#             sub_portfolios.append(sub_ptf)
#         sub_ptf.append(p)
#     # return sub_portfolios
#     return [valuation_subportfolio.s(sub_ptf, config_file) for sub_ptf in sub_portfolios]  # not calling(!), only passing a list of tasks


# @app.task(bind=True)
# def run_valuation_on_subportfolios(self, config_file: str) -> list[list[(int, str)]]:   # dict[str, list[float]]:
#     # load portfolio
#     portfolio = list(range(1, 101))

#     # split portfolio
#     sub_portfolios = []
#     count = 0
#     for p in portfolio:
#         count += 1
#         if count > 10:
#             count = 1
#         if count == 1:
#             sub_ptf = []
#             sub_portfolios.append(sub_ptf)
#         sub_ptf.append(p)
#     # return sub_portfolios

#     return chord(valuation_subportfolio.s(sub_ptf, config_file) for sub_ptf in sub_portfolios)(combine_subportflio_results.s())
#     # return [valuation_subportfolio.s(sub_ptf, config_file) for sub_ptf in sub_portfolios]  # not calling(!), only passing a list of tasks


@app.task(bind=True)
def valuation_subportfolio(self, sub_portfolio, config_file: str, job_id: str) -> int:   # dict[str, list[float]]:
    time.sleep(1)
    s = 0
    for p in sub_portfolio:
        s += p
    return s


@app.task(bind=True)
def combine_subportflio_results(self, sub_portfolio_res, job_id: str) -> int:   # dict[str, list[float]]:
    time.sleep(1)
    s = 0
    for p in sub_portfolio_res:
        s += p
    return s


def my_monitor(app: Celery) -> None:
    """ Event Monitor. """
    state = app.events.State()

    def announce_failed_tasks(event):
        # state.event(event)
        # task name is sent only with -received event, and state
        # will keep track of this for us.
        task = state.tasks.get(event['uuid'])

        print('TASK FAILED: %s[%s] %s' % (
            task.name, task.uuid, task.info(),))

    def announce_remaining(event: dict[str, Any]):
        state.event(event)

        # only process events related to a task:
        if event.get('uuid') is None:
            return

        task_id = event['uuid']
        print(event)
        # print(state.tasks)
        # # task name is sent only with -received event, and state
        # # will keep track of this for us.
        task = state.tasks.get(event['uuid'])
        db_event = {
            'hostname': event.get("hostname"),
            'pid': event.get("pid"),
            'name': event.get("name")
        }
        jobs.update_one({'_id': event['uuid']}, {'$push': {'events': event}})
        # print(task.__dict__)

        # print('TASK INFO: %s[%s] %s' % (
        #     task.name, task.uuid, task.info(),))
        jobs.update_one({f"subtasks.{task_id}": {"$exists": True}},
                        {'$push': {f"subtasks.{task_id}.events": event}})

    def task_received_handler(event: dict[str, Any]):
        """ Register subtasks with the job"""

        task_id = event['uuid']
        root_task_id = event['root_id']

        task_name = event['name']
        print(event)

        kwargs = ast.literal_eval(event['kwargs'])
        # manually extract the job_id from the kwargs object
        # kwarg_pairs = event['kwargs'][1:-1].split(",")
        # for pairs_str in kwarg_pairs:
        #     pairs_list = pairs_str.split(":")
        #     assert len(pairs_list) == 2
        #     k = pairs_list[0]
        #     v = pairs_list[1]

        #     k = k.strip()
        #     v = v.strip()
        #     if k[0] == "'" and k[-1] == "'":
        #         k = k[1:-1]
        #     if v[0] == "'" and v[-1] == "'":
        #         v = v[1:-1]
        #     kwargs[k] = v

        api_job_id = kwargs["job_id"]

        # jobs.update_one({'_id': api_job_id}, {'$push': {'subtasks': {"task_id": task_id,
        #                                                              "root_task_id": root_task_id,
        #                                                              "name": task_name,
        #                                                              "events": [],
        #                                                              }}})

        jobs.update_one({'_id': api_job_id}, {"$set": {f'subtasks.{task_id}': {"task_id": task_id,
                                                                               "root_task_id": root_task_id,
                                                                               "name": task_name,
                                                                               "events": [],
                                                                              }}})

    with app.connection() as connection:
        recv = app.events.Receiver(connection, handlers={
                'task-failed': announce_failed_tasks,
                'task-received': task_received_handler,
                '*': announce_remaining,  # state.event,
        })
        recv.capture(limit=None, timeout=None, wakeup=True)


if __name__ == "__main__":
    my_monitor(app)
