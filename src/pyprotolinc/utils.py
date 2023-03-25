
import zipfile
import os
import shutil
import tempfile

import requests


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
