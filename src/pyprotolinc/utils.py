
import zipfile
import os
import shutil
import tempfile
from datetime import datetime

import numpy as np
import numpy.typing as npt
import requests

import pyprotolinc._actuarial as actuarial  # type: ignore


class TimeAxis:
    """ TimeAxis provides vectors of the years/months/quarters to be used in the projection. """

    def __init__(self, portfolio_date: datetime, total_num_months: int) -> None:
        portfolio_year, portfolio_month = portfolio_date.year, portfolio_date.month

        # generate a time axis starting at the beginning of the month of the portfolio date
        _zero_based_months_tmp = (portfolio_month - 1) + np.arange(total_num_months + 1)
        self.months = _zero_based_months_tmp % 12 + 1
        self.years = portfolio_year + _zero_based_months_tmp // 12
        self.quarters = (self.months - 1) // 3 + 1

    def __len__(self) -> int:
        return len(self.months)


class TimeAxis2(TimeAxis):
    """ Wrapper object for the CTimeAxis that is compatible with the Python-TimeAxis"""

    def __init__(self, c_time_axis_wrapper: actuarial.CTimeAxisWrapper,
                 years: npt.NDArray[np.int16],
                 months: npt.NDArray[np.int16],
                 days: npt.NDArray[np.int16],
                 quarters: npt.NDArray[np.int16]) -> None:
        self.c_time_axis_wrapper = c_time_axis_wrapper
        self.years = years
        self.months = months
        self._days = days
        self.quarters = quarters

    def __len__(self) -> int:
        return len(self.c_time_axis_wrapper)


def download_dav_tables(target_dir: str = ".") -> None:
    """ Download DAV2004R and DAV2008T from R. Kainhofer's R-Package MortalityTables and store them
        locally in the subfolder *tables* of `target_dir`.

        :param str target_dir:  The directory where to store the downloaded datafiles.
    """

    # create a temporary dict
    with tempfile.TemporaryDirectory() as tmp_dir:

        # download location of R-package
        file_name = "MortalityTables_2.0.3.zip"
        link_address = "https://cran.r-project.org/bin/windows/contrib/4.3/" + file_name

        # download and save .zip to tmp dir
        r = requests.get(link_address)
        zip_file = os.path.join(tmp_dir, file_name)
        with open(zip_file, 'wb') as zf:
            zf.write(r.content)

        # extract zip
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)

        tables_dir = os.path.join(tmp_dir, "MortalityTables", "extdata")

        # identify files to copy
        dav_2004r_files = [f for f in os.listdir(tables_dir) if "DAV2004R" in f and f[-4:].upper() == ".CSV"]
        dav_2008t_files = [f for f in os.listdir(tables_dir) if "DAV2008T" in f and f[-4:].upper() == ".CSV"]

        # create directories if they do not exist
        dav_2004r_dir = os.path.join(target_dir, "tables", "Germany_Annuities_DAV2004R")
        dav_2008t_dir = os.path.join(target_dir, "tables", "Germany_Endowments_DAV2008T")
        os.makedirs(dav_2004r_dir, exist_ok=True)
        os.makedirs(dav_2008t_dir, exist_ok=True)

        # copy the files
        for f in dav_2004r_files:
            shutil.copy(os.path.join(tables_dir, f), os.path.join(dav_2004r_dir, f))

        # copy the files
        for f in dav_2008t_files:
            shutil.copy(os.path.join(tables_dir, f), os.path.join(dav_2008t_dir, f))
