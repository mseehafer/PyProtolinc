"""
Start a celery worker:

celery -A pyprotolinc.server.tasks worker --loglevel=INFO

"""

from typing import Any

from celery import Celery
import pymongo
import pymongo.database
import pymongo.collection
import pyprotolinc.main


# app = Celery('tasks', backend='rpc://', broker='redis://localhost')
app = Celery('tasks', broker='redis://localhost')
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


def my_monitor(app: Celery) -> None:
    """ Event Monitor. """
    state = app.events.State()

    def announce_failed_tasks(event):
        state.event(event)
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

        print(event)
        print(state.tasks)
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

    with app.connection() as connection:
        recv = app.events.Receiver(connection, handlers={
                'task-failed': announce_failed_tasks,
                '*': announce_remaining,  # state.event,
        })
        recv.capture(limit=None, timeout=None, wakeup=True)


if __name__ == "__main__":
    my_monitor(app)
