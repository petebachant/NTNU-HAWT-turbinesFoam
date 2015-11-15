#!/usr/bin/env python
"""
Generate fvOptions and topoSetDict for turbines
"""
from __future__ import division, print_function
import numpy as np
import os
import sys
import argparse


def make_fvOptions(args):
    """Create `fvOptions` from template."""
    with open("system/fvOptions.template") as f:
        template = f.read()
    with open("system/fvOptions", "w") as f:
        f.write(template.format(**args))


def make_topoSetDict(args):
    """Create `fvOptions` from template."""
    args2 = {"turbine1_upstream_x": args["turbine1_x"] - 0.25,
             "turbine1_downstream_x": args["turbine1_x"] + 0.25,
             "turbine1_tower_x": args["turbine1_x"] + 0.48,
             "turbine2_upstream_x": args["turbine2_x"] - 0.25,
             "turbine2_downstream_x": args["turbine2_x"] + 0.25,
             "turbine2_tower_x": args["turbine2_x"] + 0.14}
    with open("system/topoSetDict.template") as f:
        template = f.read()
    with open("system/topoSetDict", "w") as f:
        f.write(template.format(**args2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-parallel", nargs="?")
    parser.add_argument("--turbine1_active", default="on")
    parser.add_argument("--turbine1_x", default=0, type=float)
    parser.add_argument("--turbine1_tsr", default=6.0, type=float)
    parser.add_argument("--turbine2_active", default="on")
    parser.add_argument("--turbine2_x", default=2.682, type=float)
    parser.add_argument("--turbine2_tsr", default=4.0, type=float)

    args = vars(parser.parse_args())
    del args["parallel"]

    print("Setting turbine parameters to:")
    for k, v in args.items():
        print("    " + k + ":", v)

    make_fvOptions(args)
    make_topoSetDict(args)
