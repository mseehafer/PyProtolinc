""" Trigger a remote task:
    
    python src/pyprotolinc/server/celery_client.py

"""

from typing import Optional

import pandas as pd
from pyprotolinc.server.tasks import valuation_run



def run_distributed_job(config_file: Optional[str]=None) -> str:
    if config_file is None:
        # /home/martin/git/PyProtolinc/examples/03_mortality/config_for_cli_runner.yml
        config_file = "./examples/03_mortality/config_for_cli_runner.yml"
    res = valuation_run.delay(config_file)
    # print(pd.DataFrame(res.get()))

    # print(res.get())
    # print(res)
    print(res.id)
    return res.id


if __name__ == "__main__":
    run_distributed_job()
