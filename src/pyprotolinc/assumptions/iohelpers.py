""" Functionality to read in the assumptions tables from files. """

import logging
import yaml
import numpy as np
import pandas as pd

from pyprotolinc.riskfactors.risk_factors import get_risk_factor_by_name
from pyprotolinc.assumptions.tables import ScalarAssumptionsTable, AssumptionsTable1D, AssumptionsTable2D
from pyprotolinc.assumptions.dav2004r import DAV2004R, DAV2004R_B20
from pyprotolinc.assumptions.dav2008t import DAV2008T
from pyprotolinc.models import ModelBuilder


logger = logging.getLogger(__name__)


class WorkbookTableReader:
    """ Context Manager class to read assumption tables from
        an Excel file. """

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self._excel_file = None
        self.sheet_names = None

    def read_sheet(self, sheet_name: str):
        """ Create a Table object from the data in the sheet."""

        assert self._excel_file is not None, "Use read_sheet in with clause!"
        (values, vert_rf_name, vert_attr_values, horz_rf_name, horz_attr_values)\
            = _read_table_from_sheet(self._excel_file, sheet_name=sheet_name)

        vert_rf = get_risk_factor_by_name(vert_rf_name)
        horz_rf = get_risk_factor_by_name(horz_rf_name)

        if vert_rf is None and horz_rf is None:
            # zero-dimensional
            return ScalarAssumptionsTable(values[0, 0])
        elif vert_rf is None:
            # (here horz_rf must not be None) -> in this case transpose
            values = values.transpose()
            vert_rf = horz_rf
            horz_rf = None
            vert_attr_values = horz_attr_values
            horz_attr_values = ["DUMMY"]

        # treat the 1D/2D case
        if horz_rf is None:

            # 1D
            # validate
            vert_rf.validate_axis(vert_attr_values)

            # apply the index mapper of the risk factor
            vert_index_mapper = vert_rf.index_mapper()
            vert_attr_values_mapped = np.array([vert_index_mapper(v) for v in vert_attr_values])

            # calculate the offsets
            v_offset = vert_attr_values_mapped.min()

            return AssumptionsTable1D(values[_sort_index(vert_attr_values_mapped), :], vert_rf, offset=v_offset)
        else:
            # 2D case

            vert_rf.validate_axis(vert_attr_values)
            horz_rf.validate_axis(horz_attr_values)

            # ensure the sorting
            vert_index_mapper = vert_rf.index_mapper()
            vert_attr_values_mapped = np.array([vert_index_mapper(v) for v in vert_attr_values])
            horz_index_mapper = horz_rf.index_mapper()
            horz_attr_values_mapped = np.array([horz_index_mapper(v) for v in horz_attr_values])

            # calculate the offsets
            v_offset = vert_attr_values_mapped.min()
            h_offset = horz_attr_values_mapped.min()

            v1 = values[_sort_index(vert_attr_values_mapped), :]
            v2 = v1[:, _sort_index(horz_attr_values_mapped)]
            return AssumptionsTable2D(v2, vert_rf, horz_rf, v_offset=v_offset, h_offset=h_offset)

    def __enter__(self):
        self._excel_file = pd.ExcelFile(self.filename)
        self.sheet_names = self._excel_file.sheet_names
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self._excel_file is not None:
            self._excel_file.close()


def _read_table_from_sheet(excel_file, sheet_name):
    """ Extract data from the specified worksheet."""

    # logger.debug("Processing sheet {}".format(sheet_name))
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    # some format checks
    if df.loc[3, 0].upper() != "TABLE":
        raise Exception("Invalid format")
    if df.loc[0, 0].upper() != 'VERTICAL_RISK_FACTOR':
        raise Exception("Invalid format")
    if df.loc[1, 0].upper() != 'HORIZ_RISK_FACTOR':
        raise Exception("Invalid format")

    # read risk factor names
    vert_rf = df.loc[0, 1].upper()
    horz_rf = df.loc[1, 1].upper()
    vert_rf = None if vert_rf == 'NONE' else vert_rf
    horz_rf = None if horz_rf == 'NONE' else horz_rf

    # extract horizontal/vertical indexes headers from 3rd row
    vert_attr_values = list(df.loc[4:, 0])
    horz_attr_values = list(df.loc[3:3].values.reshape((df.shape[1],))[1:])

    values = df.values[4:, 1:].astype(np.float64)
    return (values, vert_rf, vert_attr_values, horz_rf, horz_attr_values)


def _sort_index(mapped_indexes):
    """ Return the indexes of the sorted values. """
    """ Return the indexes of the argument when sorted. """
    return np.argsort(mapped_indexes)


class AssumptionsLoaderFromConfig:
    """ Process the assumptions config files and the load the rates. """

    def __init__(self, ass_config_file_path) -> None:
        self.assumptions_spec = []
        with open(ass_config_file_path, 'r') as ass_config_file:
            ass_config = yaml.safe_load(ass_config_file)
            self.assumptions_spec = ass_config["assumptions_spec"]
        # print(self.assumptions_spec)

    def load(self, model_builder: ModelBuilder) -> None:

        self._process_be_or_res(self.assumptions_spec["be"], "be", model_builder)
        self._process_be_or_res(self.assumptions_spec["res"], "res", model_builder)

    def _process_be_or_res(self, assumptions_spec, be_or_res, model_builder: ModelBuilder) -> None:

        # collect all assumptions of type "FileTable" and
        # group them by the file name
        file_table_assumptions = {}
        for spec in assumptions_spec:

            if spec[2][0] == "FileTable":
                # creation of file table assumption providers is deferred
                from_this_file = file_table_assumptions.get(spec[2][1])
                if from_this_file is None:
                    from_this_file = []
                    file_table_assumptions[spec[2][1]] = from_this_file
                from_this_file.append((spec[0], spec[1], spec[2][2]))

            elif spec[2][0] == "DAV2004R":

                # read the remaining arguments
                kwargs = {}
                for arg in spec[2][1:]:
                    arg_split = arg.split(":")
                    kwargs[arg_split[0]] = arg_split[1]

                if "base_directory" not in kwargs:
                    raise Exception("DAV2004R requires a `base_directory` in the assumptions configuration")

                dav2004R = DAV2004R(kwargs["base_directory"])
                del kwargs["base_directory"]

                model_builder.add_transition(be_or_res, spec[0], spec[1], dav2004R.rates_provider(**kwargs))

            elif spec[2][0] == "DAV2004R_B20":

                # read the remaining arguments
                kwargs = {}
                for arg in spec[2][1:]:
                    arg_split = arg.split(":")
                    kwargs[arg_split[0]] = arg_split[1]

                if "base_directory" not in kwargs:
                    raise Exception("DAV2004R requires a `base_directory` in the assumptions configuration")

                b20 = DAV2004R_B20(kwargs["base_directory"])
                del kwargs["base_directory"]

                model_builder.add_transition(be_or_res, spec[0], spec[1], b20.rates_provider(**kwargs))

            elif spec[2][0] == "DAV2008T":

                # read the remaining arguments
                kwargs = {}
                for arg in spec[2][1:]:
                    arg_split = arg.split(":")
                    kwargs[arg_split[0]] = arg_split[1]

                if "base_directory" not in kwargs:
                    raise Exception("DAV2004R requires a `base_directory` in the assumptions configuration")

                dav2008t = DAV2008T(kwargs["base_directory"])
                del kwargs["base_directory"]

                model_builder.add_transition(be_or_res, spec[0], spec[1], dav2008t.rates_provider(**kwargs))

            elif spec[2][0] == "ScalarAssumptionsTable" or spec[2][0].upper() == "FLAT" or spec[2][0].upper() == "SCALAR":
                # assume that the next parameter is a float
                const_rate = float(spec[2][1])
                scalar_table = ScalarAssumptionsTable(const_rate)
                model_builder.add_transition(be_or_res, spec[0], spec[1], scalar_table.rates_provider())

        for assumptions_file, sheet_info in file_table_assumptions.items():
            with WorkbookTableReader(assumptions_file) as file:

                for assspec in sheet_info:
                    table = file.read_sheet(assspec[2])
                    model_builder.add_transition(be_or_res, assspec[0], assspec[1], table.rates_provider())
