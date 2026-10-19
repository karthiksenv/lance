import platform
import sys
import tempfile

import lance
import pyarrow as pa

print(platform.platform(), sys.version)
print("pylance", lance.__version__, "pyarrow", pa.__version__)
data = pa.table({
    "id": pa.array([1, 2], pa.int64()),
    "video": lance.blob_array([b"hello", b"world!"]),
})
failures = []
with tempfile.TemporaryDirectory() as tmp:
    ds = lance.write_dataset(data, f"{tmp}/clips", data_storage_version="2.2")
    queries = {
        "parent and subfield": {"columns": ["video", "video.kind"]},
        "subfield alone": {"columns": ["video.kind"]},
        "filter": {"columns": ["id"], "filter": "video.kind = 0"},
        "filter with parent": {
            "columns": ["id", "video"], "filter": "video.kind = 0"
        },
    }
    for label, kwargs in queries.items():
        try:
            result = ds.to_table(**kwargs)
            print(label, result.to_pylist())
            assert len(result) == 2
            if "video.kind" in result.column_names:
                assert result["video.kind"].to_pylist() == [0, 0]
            if "id" in result.column_names:
                assert result["id"].to_pylist() == [1, 2]
        except ValueError as exc:
            print(label, type(exc).__name__, str(exc))
            failures.append(label)
if "--expect-bug" in sys.argv:
    assert failures == ["subfield alone", "filter", "filter with parent"], failures
else:
    assert not failures, failures
