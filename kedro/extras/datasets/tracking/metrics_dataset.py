"""``MetricsDataSet`` saves data to a JSON file using an underlying
filesystem (e.g.: local, S3, GCS). It uses native json to handle the JSON file.
The ``MetricsDataSet`` is part of Kedro Experiment Tracking. The dataset is versioned by default
and only takes metrics of numeric values.
"""
import json
from typing import Any, Dict

from kedro.extras.datasets.json import JSONDataSet
from kedro.io.core import DataSetError, Version, get_filepath_str


class MetricsDataSet(JSONDataSet):
    """``MetricsDataSet`` saves data to a JSON file using an underlying
    filesystem (e.g.: local, S3, GCS). It uses native json to handle the JSON file.
    The ``MetricsDataSet`` is part of Kedro Experiment Tracking. The dataset is versioned by default
    and only takes metrics of numeric values.

        Example:
        ::

        >>> from kedro.extras.datasets.tracking import MetricsDataSet
        >>>
        >>> data = {'col1': 1, 'col2': 0.23, 'col3': 0.002}
        >>>
        >>> # data_set = MetricsDataSet(filepath="gcs://bucket/test.json")
        >>> data_set = MetricsDataSet(filepath="test.json")
        >>> data_set.save(data)
        >>> reloaded = data_set.load()
        >>> assert data == reloaded

    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        filepath: str,
        save_args: Dict[str, Any] = None,
        version: Version = Version(None, None),
        credentials: Dict[str, Any] = None,
        fs_args: Dict[str, Any] = None,
    ) -> None:
        """Creates a new instance of ``MetricsDataSet`` pointing to a concrete JSON file
        on a specific filesystem.

        Args:
            filepath: Filepath in POSIX format to a JSON file prefixed with a protocol like `s3://`.
                If prefix is not provided, `file` protocol (local filesystem) will be used.
                The prefix should be any protocol supported by ``fsspec``.
                Note: `http(s)` doesn't support versioning.
            save_args: json options for saving JSON files (arguments passed
                into ```json.dump``). Here you can find all available arguments:
                https://docs.python.org/3/library/json.html
                All defaults are preserved, but "default_flow_style", which is set to False.
            version: If specified, should be an instance of
                ``kedro.io.core.Version``. If its ``load`` attribute is
                None, the latest version will be loaded. If its ``save``
                attribute is None, save version will be autogenerated.
                Versioning for this dataset is turned on by default and can not be turned off.
            credentials: Credentials required to get access to the underlying filesystem.
                E.g. for ``GCSFileSystem`` it should look like `{"token": None}`.
            fs_args: Extra arguments to pass into underlying filesystem class constructor
                (e.g. `{"project": "my-project"}` for ``GCSFileSystem``), as well as
                to pass to the filesystem's `open` method through nested keys
                `open_args_load` and `open_args_save`.
                Here you can find all available arguments for `open`:
                https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem.open
                All defaults are preserved, except `mode`, which is set to `r` when loading
                and to `w` when saving.
        """
        super().__init__(
            filepath=filepath,
            save_args=save_args,
            credentials=credentials,
            version=version,
            fs_args=fs_args,
        )

    def _load(self) -> Dict:
        raise DataSetError(f"Loading not supported for `{self.__class__.__name__}`")

    def _save(self, data: Dict[str, float]) -> None:
        """Converts all values in the data from a ``MetricsDataSet`` to float to make sure
        they are numeric values which can be displayed in Kedro Viz and then saves the dataset.
        """
        try:
            for key, value in data.items():
                data[key] = float(value)
        except ValueError as exc:
            raise DataSetError(
                f"The MetricsDataSet expects only numeric values. {exc}"
            ) from exc

        save_path = get_filepath_str(self._get_save_path(), self._protocol)

        with self._fs.open(save_path, **self._fs_open_args_save) as fs_file:
            json.dump(data, fs_file, **self._save_args)

        self._invalidate_cache()