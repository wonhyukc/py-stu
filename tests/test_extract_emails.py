import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from bin.extract_emails import get_subfolder_path

def test_get_subfolder_path():
    assert get_subfolder_path("py", "7") == "output/py07"
    assert get_subfolder_path("web1", "7") == "output/web1_07"
    assert get_subfolder_path("web2", "7") == "output/web2_07"
    assert get_subfolder_path("unknown", "7") == "output/unknown07"
    assert get_subfolder_path("py", None) == "output/py_all"
