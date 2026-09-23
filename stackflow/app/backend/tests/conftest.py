import os
import sys
import tempfile
from pathlib import Path

# Isolate every test run: the real forward record and app data are never touched by tests.
_tmp = Path(tempfile.mkdtemp(prefix="drift_test_"))
os.environ["DRIFT_DATA_DIR"] = str(_tmp / "data")
os.environ["DRIFT_FORWARD_RECORD"] = str(_tmp / "forward_record_test.csv")
os.environ["DRIFT_SCHEDULER"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
