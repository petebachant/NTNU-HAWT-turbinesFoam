#!/usr/bin/env python
"""This script plots results from the NTNU HAWT turbinesFoam simulation."""

import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from pynhtf.processing import *
from pynhtf.plotting import *
import argparse


if __name__ == "__main__":
    import seaborn
    seaborn.set(color_codes=True)

    parser = argparse.ArgumentParser(description="Generate plots.")
    parser.add_argument("plot", nargs="*", help="What to plot", default="perf",
                        choices=["perf", "wake", "spanwise", "blade-perf",
                                 "strut-perf", "perf-curves", "perf-curves-exp",
                                 "recovery", "meancontquiv"])
    parser.add_argument("--all", "-A", help="Generate all figures",
                        default=False, action="store_true")
    parser.add_argument("--save", "-s", help="Save to `figures` directory",
                        default=False, action="store_true")
    parser.add_argument("--no-show", default=False, action="store_true",
                        help="Do not call matplotlib show function")
    parser.add_argument("-q", help="Quantities to plot", nargs="*",
                        default=["alpha", "rel_vel_mag"])
    args = parser.parse_args()

    if args.save:
        if not os.path.isdir("figures"):
            os.mkdir("figures")

    if "wake" in args.plot or args.all:
        plot_profiles(save=args.save)
    if "perf" in args.plot or args.all:
        plot_cp(save=args.save)
    if "spanwise" in args.plot or args.all:
        plot_spanwise(save=args.save)
    if "blade-perf" in args.plot or args.all:
        plot_blade_perf(save=args.save)
    if "strut-perf" in args.plot or args.all:
        plot_strut_perf(save=args.save)
    if "perf-curves" in args.plot or args.all:
        plot_perf_curves(exp=False, save=args.save)
    if "perf-curves-exp" in args.plot or args.all:
        plot_perf_curves(exp=True, save=args.save)
    if "recovery" in args.plot or args.all:
        make_recovery_bar_chart(save=args.save)
    if "meancontquiv" in args.plot:
        plot_meancontquiv(save=args.save)

    if not args.no_show:
        plt.show()
