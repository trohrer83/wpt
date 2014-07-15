# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os
import sys

import config

def abs_path(path):
    return os.path.abspath(os.path.expanduser(path))


def slash_prefixed(url):
    if not url.startswith("/"):
        url = "/" + url
    return url


def require_arg(kwargs, name, value_func=None):
    if value_func is None:
        value_func = lambda x: x is not None

    if not name in kwargs or not value_func(kwargs[name]):
        print >> sys.stderr, "Missing required argument %s" % name
        sys.exit(1)


def create_parser(allow_mandatory=True):
    from mozlog.structured import commandline

    import products

    config_data = config.load()

    parser = argparse.ArgumentParser("web-platform-tests",
                                     description="Runner for web-platform-tests tests.")
    parser.add_argument("--metadata", action="store", type=abs_path, dest="metadata_root",
                        help="Path to the folder containing test metadata"),
    parser.add_argument("--tests", action="store", type=abs_path, dest="tests_root",
                        help="Path to web-platform-tests"),
    parser.add_argument("--prefs-root", dest="prefs_root", action="store", type=abs_path,
                        help="Path to the folder containing browser prefs"),
    parser.add_argument("--config", action="store", type=abs_path,
                        default=config.path(check_argv=False), help="Path to config file")
    parser.add_argument("--binary", action="store",
                        type=abs_path, help="Binary to run tests against")
    parser.add_argument("--test-types", action="store",
                        nargs="*", default=["testharness", "reftest"],
                        choices=["testharness", "reftest"],
                        help="Test types to run")
    parser.add_argument("--processes", action="store", type=int, default=1,
                        help="Number of simultaneous processes to use")
    parser.add_argument("--include", action="append", type=slash_prefixed,
                        help="URL prefix to include")
    parser.add_argument("--exclude", action="append", type=slash_prefixed,
                        help="URL prefix to exclude")
    parser.add_argument("--include-manifest", type=abs_path,
                        help="Path to manifest listing tests to include")

    parser.add_argument("--total-chunks", action="store", type=int, default=1,
                        help="Total number of chunks to use")
    parser.add_argument("--this-chunk", action="store", type=int, default=1,
                        help="Chunk number to run")
    parser.add_argument("--chunk-type", action="store", choices=["none", "equal_time", "hash"],
                        default="none", help="Chunking type to use")

    parser.add_argument("--list-test-groups", action="store_true",
                        default=False,
                        help="List the top level directories containing tests that will run.")
    parser.add_argument("--list-disabled", action="store_true",
                        default=False,
                        help="List the tests that are disabled on the current platform")

    parser.add_argument("--timeout-multiplier", action="store", type=float, default=None,
                        help="Multiplier relative to standard test timeout to use")
    parser.add_argument("--repeat", action="store", type=int, default=1,
                        help="Number of times to run the tests")

    parser.add_argument("--no-capture-stdio", action="store_true", default=False,
                        help="Don't capture stdio and write to logging")

    parser.add_argument("--product", action="store", choices=products.products_enabled(config_data),
                        default="firefox", help="Browser against which to run tests")

    parser.add_argument('--debugger',
                        help="run under a debugger, e.g. gdb or valgrind")
    parser.add_argument('--debugger-args', help="arguments to the debugger")
    parser.add_argument('--pause-on-unexpected', action="store_true",
                        help="Halt the test runner when an unexpected result is encountered")

    parser.add_argument("--b2g-no-backup", action="store_true", default=False,
                        help="Don't backup device before testrun with --product=b2g")

    commandline.add_logging_group(parser)
    return parser


def set_from_config(kwargs):
    kwargs["config"] = config.read(kwargs["config"])

    keys = {"paths": [("tests", "tests_root"), ("metadata", "metadata_root")],
            "web-platform-tests": ["remote_url", "branch", "sync_path"]}

    for section, values in keys.iteritems():
        for value in values:
            if type(value) in (str, unicode):
                config_value, kw_value = value, value
            else:
                config_value, kw_value = value
            if kw_value in kwargs and kwargs[kw_value] is None:
                kwargs[kw_value] = kwargs["config"].get(section, {}).get(config_value, None)

def check_args(kwargs):
    from mozrunner import cli

    set_from_config(kwargs)

    if kwargs["this_chunk"] > 1:
        require_arg(kwargs, "total_chunks", lambda x: x >= kwargs["this_chunk"])

        if kwargs["chunk_type"] == "none":
            kwargs["chunk_type"] = "equal_time"

    if kwargs["debugger"] is not None:
        debug_args, interactive = cli.debugger_arguments(kwargs["debugger"],
                                                         kwargs["debugger_args"])
        if interactive:
            require_arg(kwargs, "processes", lambda x: x == 1)
            kwargs["no_capture_stdio"] = True
        kwargs["interactive"] = interactive
        kwargs["debug_args"] = debug_args
    else:
        kwargs["interactive"] = False
        kwargs["debug_args"] = None

    return kwargs


def create_parser_update(allow_mandatory=True):
    config_data = config.load()

    parser = argparse.ArgumentParser("web-platform-tests-update",
                                     description="Update script for web-platform-tests tests.")
    parser.add_argument("--metadata", action="store", type=abs_path, dest="metadata_root",
                        help="Path to the folder containing test metadata"),
    parser.add_argument("--tests", action="store", type=abs_path, dest="tests_root",
                        help="Path to web-platform-tests"),
    parser.add_argument("--sync-path", action="store", type=abs_path,
                        help="Path to store git checkout of web-platform-tests during update"),
    parser.add_argument("--remote_url", action="store",
                        help="URL of web-platfrom-tests repository to sync against"),
    parser.add_argument("--branch", action="store", type=abs_path,
                        help="Remote branch to sync against")
    parser.add_argument("--config", action="store", type=abs_path,
                        default=config.path(check_argv=False), help="Path to config file")
    parser.add_argument("--rev", action="store", help="Revision to sync to")
    parser.add_argument("--no-check-clean", action="store_true", default=False,
                        help="Don't check the working directory is clean before updating")
    parser.add_argument("--patch", action="store_true",
                        help="Create an mq patch or git branch+commit containing the changes.")
    parser.add_argument("--sync", dest="sync", action="store_true", default=False,
                        help="Sync the tests with the latest from upstream")
    parser.add_argument("--ignore-existing", action="store_true", help="When updating test results only consider results from the logfiles provided, not existing expectations.")
    # Should make this required iff run=logfile
    parser.add_argument("run_log", nargs="*", type=abs_path,
                        help="Log file from run of tests")
    return parser


def create_parser_reduce(allow_mandatory=True):
    parser = create_parser(allow_mandatory)
    parser.add_argument("target", action="store", help="Test id that is unstable")
    return parser


def parse_args():
    parser = create_parser()
    rv = vars(parser.parse_args())
    check_args(rv)
    return rv

def parse_args_update():
    parser = create_parser_update()
    rv = vars(parser.parse_args())
    set_from_config(rv)
    return rv

def parse_args_reduce():
    parser = create_parser_reduce()
    rv = vars(parser.parse_args())
    check_args(rv)
    return rv
