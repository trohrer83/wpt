import ConfigParser
import os
import sys

here = os.path.split(__file__)[0]

class ConfigDict(dict):
    def __init__(self, base_path, *args, **kwargs):
        self.base_path = base_path
        dict.__init__(self, *args, **kwargs)

    def get_path(self, key):
        pwd = os.path.abspath(os.path.curdir)
        path = self[key]
        os.path.expanduser(path)
        return os.path.join(self.base_path, path)

def read(config_path):
    config_path = os.path.abspath(config_path)
    config_root = os.path.split(config_path)[0]
    parser = ConfigParser.SafeConfigParser()
    success = parser.read(config_path)
    assert config_path in success, success

    subns = {"pwd": os.path.abspath(os.path.curdir)}

    rv = {}
    for section in parser.sections():
        rv[section] = ConfigDict(config_root)
        for key in parser.options(section):
            rv[section][key] = parser.get(section, key, False, subns)

    return rv

def path(check_argv=True):
    path = None
    if check_argv:
        for i, arg in enumerate(sys.argv):
            if arg == "--config":
                if i + 1 < len(sys.argv):
                    path = sys.argv[i+1]
                elif arg.startswith("--config="):
                    path = arg.split("=", 1)[1]
                if path is not None:
                    break

    if path is None:
        if os.path.exists("wptrunner.ini"):
            path = os.path.abspath("wptrunner.ini")
        else:
            path = os.path.join(here, "..", "wptrunner.default.ini")

    return path

def load():
    return read(path())
