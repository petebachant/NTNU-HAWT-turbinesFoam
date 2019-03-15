#!/usr/bin/env python
"""Script for running the NTNU HAWT case."""

import argparse
import os
import subprocess
from subprocess import call, check_output
import numpy as np
import pandas as pd
import glob
import foampy
from foampy.dictionaries import replace_value
import shutil
from pynhtf import processing as pr


def get_mesh_dims():
    """Get mesh dimensions by grepping `blockMeshDict`."""
    raw = check_output("grep blocks system/blockMeshDict -A3",
                       shell=True).decode().split("\n")[3]
    raw = raw.replace("(", "").replace(")", "").split()
    return {"nx": int(raw[0]), "ny": int(raw[1]), "nz": int(raw[2])}


def get_dt():
    """Read ``deltaT`` from ``controlDict``."""
    return foampy.dictionaries.read_single_line_value("controlDict",
                                                      keyword="deltaT")


def get_nacelle_ano_vals():
    """Lookup sampled nacelle anemometer values."""
    res = {}
    # TODO


def log_results(param="turbine1_yaw", append=True):
    """Log results to CSV file."""
    if not os.path.isdir("processed"):
        os.mkdir("processed")
    fpath = "processed/{}_sweep.csv".format(param)
    if append and os.path.isfile(fpath):
        df = pd.read_csv(fpath)
    else:
        df = pd.DataFrame(columns=["nx", "ny", "nz", "dt", "tsr", "cp", "cd"])
    d = pr.calc_perf()
    d.update(get_mesh_dims())
    d["dt"] = get_dt()
    # TODO: Add nacelle anemometer params and results
    df = df.append(d, ignore_index=True)
    df.to_csv(fpath, index=False)


def set_blockmesh_resolution(nx=48, ny=None, nz=None):
    """Set mesh resolution in ``blockMeshDict``.

    If only ``nx`` is provided, the default resolutions for other dimensions are
    scaled proportionally.
    """
    defaults = {"nx": 48, "ny": 48, "nz": 32}
    if ny is None:
        ny = nx
    if nz is None:
        nz = int(nx*defaults["nz"]/defaults["nx"])
    print("Setting blockMesh resolution to ({} {} {})".format(nx, ny, nz))
    foampy.fill_template("system/blockMeshDict.template", nx=nx, ny=ny, nz=nz)


def set_dt(dt=0.01, tsr=None, tsr_0=6.0, write_interval=None, les=False):
    """Set ``deltaT`` in ``controlDict``. Will scale proportionally if ``tsr``
    and ``tsr_0`` are supplied, such that steps-per-rev is consistent with
    ``tsr_0``.
    """
    if tsr is not None:
        dt = dt*tsr_0/tsr
        print("Setting deltaT = dt*tsr_0/tsr = {:.3f}".format(dt))
    dt = str(dt)
    if write_interval is None:
        if les:
            write_interval = 0.01
        else:
            write_interval = 0.05
    foampy.fill_template("system/controlDict.template", dt=dt,
                         write_interval=write_interval)


def gen_sets_file(origin=(0.1, 0.0, 0.1), delta=0.1, yaw=0):
    """Generate ``sets`` file for post-processing nacelle anemometer
    locations.
    """
    # Input parameters
    setformat = "raw"
    interpscheme = "cellPoint"
    fields = ["UMean"]
    x = 1.0
    ymax = 1.5
    ymin = -1.5
    zmax = 1.125
    zmin = -1.125
    z_array = np.linspace(zmin, zmax, nz)
    txt = "\ntype sets;\n"
    txt +='libs ("libsampling.so");\n'
    txt += "setFormat " + setformat + ";\n"
    txt += "interpolationScheme " + interpscheme + ";\n\n"
    txt += "sets \n ( \n"
    for z in z_array:
        # Fix interpolation issues if directly on a face
        if z == 0.0:
            z += 1e-5
        txt += "    " + "profile_" + str(z) + "\n"
        txt += "    { \n"
        txt += "        type        uniform; \n"
        txt += "        axis        y; \n"
        txt += "        start       (" + str(x) + " " + str(ymin) + " " \
            + str(z) + ");\n"
        txt += "        end         (" + str(x) + " " + str(ymax) + " " \
            + str(z) + ");\n"
        txt += "        nPoints     " + str(ny) + ";\n    }\n\n"
    txt += ");\n\n"
    txt += "fields \n(\n"
    for field in fields:
        txt += "    " + field + "\n"
    txt += "); \n\n"
    txt += "//\
     *********************************************************************** //\
     \n"
    with open("system/sets", "w") as f:
        f.write(txt)


def post_process(parallel=False, tee=False, reconstruct=False, overwrite=True):
    """Execute all post-processing."""
    gen_sets_file()
    foampy.run("postProcess", args="-func -vorticity", parallel=parallel,
               logname="log.vorticity", tee=tee, overwrite=overwrite)
    foampy.run("postProcess", args="-dict system/controlDict.recovery "
               " -latestTime", parallel=parallel, logname="log.recovery",
               tee=tee, overwrite=overwrite)
    # Reconstruct if necessary so sampling isn't run in parallel
    if reconstruct:
        foampy.run("reconstructPar", args="-latestTime", overwrite=overwrite,
                   logname="log.reconstructPar-latestTime", tee=tee)
    foampy.run("postProcess", args="-func sets -latestTime",
               logname="log.sample", parallel=False, overwrite=overwrite,
               tee=tee)


def param_sweep(param="turbine1_yaw", start=-20, stop=21, step=5,
                dtype=float, append=False, parallel=True, tee=False, **kwargs):
    """Run multiple simulations, varying ``param``.

    ``stop`` is not included.
    """
    print("Running {} sweep".format(param))
    fpath = "processed/{}_sweep.csv".format(param)
    if not append and os.path.isfile(fpath):
        os.remove(fpath)
    if param == "nx":
        dtype = int
    param_list = np.arange(start, stop, step, dtype=dtype)
    for p in param_list:
        print("Running with {} = {}".format(param, p))
        if p == param_list[0] or param == "nx":
            foampy.clean(remove_zero=True)
            mesh = True
        else:
            mesh = False
        # Update kwargs for this value
        kwargs.update({param: p})
        run(parallel=parallel, tee=tee, mesh=mesh, reconstruct=False,
            post=False, **kwargs)
        os.rename("log.pimpleFoam", "log.pimpleFoam." + str(p))
        log_results(param=param, append=True)
        foampy.clean(leave_mesh=True, remove_zero=True)


def set_turbine_params(turbine1_tsr=6, turbine1_active="on", turbine1_x=0,
                       turbine2_tsr=4, turbine2_active="on", turbine2_x=2.682,
                       turbine1_yaw=0, turbine2_yaw=0, verbose=True):
    """Write file defining turbine operating parameters.

    ``tsr_phase`` is in radians.
    """
    args2 = {"turbine1_upstream_x": turbine1_x - 0.25,
             "turbine1_downstream_x": turbine1_x + 0.25,
             "turbine1_tower_x": turbine1_x + 0.48,
             "turbine2_upstream_x": turbine2_x - 0.25,
             "turbine2_downstream_x": turbine2_x + 0.25,
             "turbine2_tower_x": turbine2_x + 0.14}
    foampy.fill_template("system/topoSetDict.template", **args2)
    params = {"turbine1_tsr": turbine1_tsr,
              "turbine1_active": turbine1_active,
              "turbine1_x": turbine1_x,
              "turbine1_yaw": turbine1_yaw,
              "turbine2_tsr": turbine2_tsr,
              "turbine2_active": turbine2_active,
              "turbine2_x": turbine2_x,
              "turbine2_yaw": turbine2_yaw}
    if verbose:
        print("Setting turbine params as:")
        for k, v in params.items():
            print("    " + k + ":", v)
    foampy.fill_template("system/fvOptions.template", **params)


def run(turbine1_tsr=6, turbine1_active="on", turbine1_x=0,
        turbine2_tsr=4, turbine2_active="on", turbine2_x=2.682,
        turbine1_yaw=0, turbine2_yaw=0,
        mesh=True, parallel=False, tee=False, reconstruct=True,
        overwrite=False, post=False, write_interval=None):
    """Run simulation once."""
    set_turbine_params(turbine1_tsr=turbine1_tsr,
                       turbine1_active=turbine1_active,
                       turbine1_x=turbine1_x,
                       turbine2_tsr=turbine2_tsr,
                       turbine2_active=turbine2_active,
                       turbine2_x=turbine2_x,
                       turbine1_yaw=turbine1_yaw,
                       turbine2_yaw=turbine2_yaw)
    if mesh:
        foampy.run("blockMesh", tee=tee)
    # Copy over initial conditions
    subprocess.call("cp -rf 0.orig 0 > /dev/null 2>&1", shell=True)
    if parallel and not glob.glob("processor*"):
        foampy.run("decomposePar", tee=tee)
        subprocess.call("for PROC in processor*; do cp -rf 0.orig/* $PROC/0; "
                        " done", shell=True)
    if mesh:
        foampy.run("snappyHexMesh", args="-overwrite", tee=tee,
                   parallel=parallel)
        foampy.run("topoSet", parallel=parallel, tee=tee)
        if parallel:
            foampy.run("reconstructParMesh", args="-constant -time 0", tee=tee)
    foampy.run("pimpleFoam", parallel=parallel, tee=tee, overwrite=overwrite)
    if parallel and reconstruct:
        foampy.run("reconstructPar", tee=tee, overwrite=overwrite)
    if post:
        post_process(overwrite=overwrite, parallel=parallel,
                     reconstruct=not reconstruct)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run NTNU HAWT ALM case")
    parser.add_argument("--turbine1-active", default="on")
    parser.add_argument("--turbine1-x", default=0, type=float)
    parser.add_argument("--turbine1-tsr", default=6.0, type=float)
    parser.add_argument("--turbine1-yaw", default=0.0, type=float)
    parser.add_argument("--turbine2-active", default="on")
    parser.add_argument("--turbine2-x", default=2.682, type=float)
    parser.add_argument("--turbine2-tsr", default=4.0, type=float)
    parser.add_argument("--turbine2-yaw", default=0.0, type=float)
    parser.add_argument("--leave-mesh", "-l", default=False,
                        action="store_true", help="Leave existing mesh")
    parser.add_argument("--post", "-P", default=False, action="store_true",
                        help="Run post-processing (done by default at end of "
                             " run)")
    parser.add_argument("--param-sweep", "-p",
                        help="Run multiple simulations varying a parameter",
                        choices=["turbine1_tsr", "turbine2_tsr",
                                 "turbine1_yaw", "turbine2_yaw"])
    parser.add_argument("--start", default=-20, type=float)
    parser.add_argument("--stop", default=21, type=float)
    parser.add_argument("--step", default=5, type=float)
    parser.add_argument("--serial", "-S", default=False, action="store_true")
    parser.add_argument("--append", "-a", default=False, action="store_true")
    parser.add_argument("--tee", "-T", default=False, action="store_true",
                        help="Print log files to terminal while running")
    parser.add_argument("--overwrite", "-f", default=False, action="store_true",
                        help="Clean case automatically before running")
    args = parser.parse_args()

    if args.param_sweep:
        param_sweep(args.param_sweep, args.start, args.stop, args.step,
                    append=args.append, parallel=not args.serial, tee=args.tee,
                    turbine1_active=args.turbine1_active,
                    turbine1_tsr=args.turbine1_tsr,
                    turbine1_x=args.turbine1_x,
                    turbine1_yaw=args.turbine1_yaw,
                    turbine2_active=args.turbine2_active,
                    turbine2_tsr=args.turbine2_tsr,
                    turbine2_x=args.turbine2_x,
                    turbine2_yaw=args.turbine2_yaw)
    elif not args.post:
        run(turbine1_active=args.turbine1_active,
            turbine1_tsr=args.turbine1_tsr,
            turbine1_x=args.turbine1_x,
            turbine1_yaw=args.turbine1_yaw,
            turbine2_active=args.turbine2_active,
            turbine2_tsr=args.turbine2_tsr,
            turbine2_x=args.turbine2_x,
            turbine2_yaw=args.turbine2_yaw,
            parallel=not args.serial,
            tee=args.tee,
            mesh=not args.leave_mesh,
            overwrite=args.leave_mesh)
    if args.post:
        post_process(parallel=not args.serial, tee=args.tee,
                     overwrite=args.overwrite)
