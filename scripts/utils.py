import logging

import pandas as pd
import pyam
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_yaml_file(file_path):
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    return data


class Validation:
    def __init__(self, db, definitions_path):
        """
        Initialize the Validation object.

        Args:
            db (pyam.IamDataFrame): The input database.
            definitions_path (str): The path to the YAML file containing the filter definitions.

        Returns:
            None
        """
        self.db = db
        self.definitions = read_yaml_file(definitions_path)

    def create_validation_columns(self, region_level="World", generate_summary=False):
        """
        Creates validation columns for each key in the definitions dictionary.

        Args:
            region_level (str, optional): The region level for which the validation columns are created. Defaults to "World".
            generate_summary (bool, optional): Flag indicating whether to generate a summary of the validation columns. Defaults to False.
        """
        validation_columns = []
        for key in self.definitions:
            proxy_variable = self.definitions[key]["variable"]
            logger.info(
                f"Creating validation column for {key} using defined proxy {proxy_variable}"
            )
            try:
                missing_data = (
                    self.db.require_data(region=region_level, variable=proxy_variable)
                    .set_index(["model", "scenario"])
                    .index
                )
            except:
                missing_data = None
            meta_column = f"validation_{key}"
            self.db.set_meta(name=meta_column, meta=True)
            if missing_data is not None:
                self.db.set_meta(name=meta_column, meta=False, index=missing_data)
            validation_columns.append(meta_column)
        if generate_summary:
            self.summary = self.db.meta[validation_columns].value_counts()


class Filters:
    def __init__(self, db, definitions_path):
        self.db = db
        self.definitions = read_yaml_file(definitions_path)

    def _check_for_validation_column(self):
        """
        Checks if the validation columns exist in the metadata table.

        This function iterates over the keys in the `definitions` dictionary and checks if the corresponding
        validation column exists in the metadata table. If any validation column is missing, a `ValueError` is raised
        with a message indicating the missing column.

        Raises:
            ValueError: If any validation column is missing in the metadata table.
        """
        meta_columns = self.db.meta.columns
        for key in self.definitions.keys():
            expected_validation_column = f"validation_{key}"
            if expected_validation_column not in meta_columns:
                raise ValueError(
                    f"Please perform validation. Missing the following columns: {expected_validation_column}"
                )

    def apply_filters(self):
        self._check_for_validation_column()
        for key in self.definitions.keys():
            logger.info(f"Preparing filter sets for {key}")
            self.db.set_meta(name=f"pass_{key}", meta=True)
            passing_scens = (
                self.db.validate(
                    variable=self.definitions[key]["variable"],
                    **self.definitions[key]["criteria"],
                )
                .set_index(["model", "scenario"])
                .index.unique()
            )
            self.db.set_meta(name=f"pass_{key}", meta=False, index=passing_scens)

    def apply_categories(self):
        self._check_for_validation_column()
        for key, data in self.definitions.items():
            if "categorize" not in data:
                continue
            logger.info(f"Preparing categorization for {key}")

            args = data["categorize"]
            self.db.categorize(
                args["name"],
                args["label"],
                variable=data["variable"],
                **data["criteria"],
                **{k: v for k, v in args.items() if k not in ["name", "label"]},
            )
