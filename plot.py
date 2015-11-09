#!/usr/bin/env python
"""
This script plots results from the NTNU HAWT turbinesFoam simulation.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from pynhtf.processing import *
from pynhtf.plotting import *


if __name__ == "__main__":
    import seaborn as sns
    sns.set(context="paper", style="white", font_scale=1.5,
            rc={"axes.grid": True, "legend.frameon": True})

    if len(sys.argv) > 1:
        if sys.argv[1] == "wake":
            plot_meancontquiv()
        elif sys.argv[1] == "perf":
            plot_cp()
        elif sys.argv[1] == "blade":
            plot_blade_perf()
        elif sys.argv[1] == "spanwise":
            plot_spanwise()
    else:
        plot_cp()
    plt.show()
