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
    """Create `fvOptions` for turbines from template."""
    print("Generating fvOptions with:")
    for k, v in args.items():
        print("    " + k + ":", v)
    with open("system/fvOptions.template") as f:
        template = f.read()
    with open("system/fvOptions", "w") as f:
        f.write(template.format(**args))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--turbine1_active", default="on")
    parser.add_argument("--turbine1_x", default=0)
    parser.add_argument("--turbine1_tsr", default=6.0)
    parser.add_argument("--turbine2_active", default="on")
    parser.add_argument("--turbine2_x", default=2.682)
    parser.add_argument("--turbine2_tsr", default=4.0)

    args = parser.parse_args()

    make_fvOptions(vars(args))
