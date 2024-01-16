""" Trigger a remote task:

    python src/pyprotolinc/server/celery_client.py

"""

from typing import Optional

from celery import chord, chain, group

from pyprotolinc.server.tasks import valuation_run, valuation_run_modular


def run_distributed_job(config_file: Optional[str] = None) -> str:
    if config_file is None:
        # /home/martin/git/PyProtolinc/examples/03_mortality/config_for_cli_runner.yml
        config_file = "./examples/03_mortality/config_for_cli_runner.yml"
    res = valuation_run.delay(config_file)
    # print(pd.DataFrame(res.get()))

    # print(res.get())
    # print(res)
    print(res.id)
    return res.id


def run_distributed_job_test(job_id: str, config_file: Optional[str] = None) -> str:

    task_id = valuation_run_modular.s(config_file, job_id=job_id).delay()
    # res = task.get()
    # print(res)
    return task_id.id


# def run_distributed_job_test2(config_file: Optional[str] = None) -> int:

#     # load portfolio and split it
#     # sub_portfolios = load_and_splitportfolio.delay(config_file).get()

#     list_val_tasks = load_and_splitportfolio.s(config_file).delay()

#     list_val_tasks = list_val_tasks.get()
#     print("list_val_tasks", list_val_tasks)

#     workflow = chord(list_val_tasks)(combine_subportflio_results.s())

#     # # run valuation for each subportfolio (in parallel)
#     # workflow = chord(group(valuation_subportfolio.s(sub_ptf, config_file) for sub_ptf in sub_portfolios),
#     #                  combine_subportflio_results.s())
#     res = workflow.get()
#     return res


if __name__ == "__main__":
    run_distributed_job()


# [['aa35563a-0540-4e3e-9fd1-0154f7d4f9f1',  # combine
#   [['3a295af0-1aa9-4257-9442-dce3dad65538', None],     # somehow represent the group?
#    [[['116f3895-be60-48cc-8203-73854fab620a', None], None],   # valuation subpt
#     [['d030aa38-db39-4f76-9590-20e29dfc59cf', None], None],
#     [['0c28ca0e-1b61-4e2b-b637-0edd5fdbd26d', None], None],
#     [['46bb7a6f-2bb5-497e-a270-b9daf6175d6c', None], None],
#     [['88b7fe1b-dca2-4530-8b4f-1689f024beca', None], None],
#     [['d80e3e0c-9525-412f-ae3d-9c529cad6f01', None], None],
#     [['5fe26e8d-94bb-4891-8ec1-002aaccb4591', None], None],
#     [['99c8cbdf-1e69-41c8-8be3-416ec0bf7c0e', None], None],
#     [['04d83481-8e23-4e42-a39c-5ca732c66442', None], None],
#     [['a057dad3-02ff-4597-836e-c8116ef32561', None], None]]
#     ]
# ], None]

# [['1c1c70e3-e891-4ee8-bf9f-7ffb0048aa11', [['ebc8efe2-7bb7-47e2-945e-0018175dbf4b', None], [[['dfeb09d7-be13-4899-be6c-15269c34d545', None], None], [['2e334989-497f-45aa-b560-f2aa3c46d1df', None], None], [['7f1012e1-9670-4b35-8cf2-67c59ae24799', None], None], [['0151c55f-c636-48d1-a6a2-34eef5723e88', None], None], [['3cb928a2-a385-4b21-b4f6-6b8b6bcd57e5', None], None], [['6c493cf1-5923-45b0-a56d-b7a06d3ab9ba', None], None], [['cb54016f-3213-4f9f-bf69-e12d1fc6edb3', None], None], [['603906e7-be85-416a-88f6-4545f36683af', None], None], [['bc4850aa-6c99-4f3d-a03d-54c62d742c62', None], None], [['2c9a5441-39ec-434b-9356-c8748c415f55', None], None]]]], None]