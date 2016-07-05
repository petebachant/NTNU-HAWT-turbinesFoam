#!/usr/bin/env python
"""Processing functions."""

from __future__ import division, print_function
import matplotlib.pyplot as plt
import re
import numpy as np
import os
import sys
import foampy
from pxl import fdiff
import pandas as pd

# Some constants
D = {"turbine1": 0.944, "turbine2": 0.894, "nominal": 0.9}
R = {turbine: d/2 for turbine, d in D.items()}
A = {turbine: np.pi*r**2 for turbine, r in R.items()}
U = 10.0
U_infty = U
rho = 1.2


def load_u_profile(turbine="turbine2", z_R=0.0):
    """Load data from the sampled mean velocity and return it as a pandas
    `DataFrame`.
    """
    z_R = float(z_R)
    timedirs = os.listdir("postProcessing/sets")
    latest_time = max(timedirs)
    fname = "{}_{}_UMean.csv".format(turbine, z_R)
    data = pd.read_csv(os.path.join("postProcessing", "sets", latest_time,
                       fname))
    df = pd.DataFrame()
    df["y_R"] = data["y"]/R[turbine]
    df["u"] = data["UMean_0"]
    return df


def load_vel_map(turbine="turbine2", component="u"):
    """Load all mean streamwise velocity profiles. Returns a `DataFrame` with
    `z_R` as the index and `y_R` as columns.
    """
    # Define columns in set raw data file
    columns = dict(u=0, v=1, w=2)
    sets_dir = os.path.join("postProcessing", "sets")
    latest_time = max(os.listdir(sets_dir))
    data_dir = os.path.join(sets_dir, latest_time)
    flist = os.listdir(data_dir)
    z_R = []
    for fname in flist:
        if "UMean" in fname:
            z_R.append(float(fname.split("_")[1]))
    z_R.sort()
    z_R.reverse()
    vel = []
    for zi in z_R:
        fname = "{}_{}_UMean.csv".format(turbine, zi)
        dfi = pd.read_csv(os.path.join(data_dir, fname))
        vel.append(dfi["UMean_{}".format(columns[component])].values)
    y_R = dfi["y"]/R[turbine]
    z_R = np.asarray(z_R)
    vel = np.asarray(vel).reshape((len(z_R), len(y_R)))
    df = pd.DataFrame(vel, index=z_R, columns=y_R)
    return df


def load_k_profile(turbine="turbine2", z_R=0.0):
    """Load data from the sampled `UPrime2Mean` and `kMean` (if available) and
    return it as a pandas `DataFrame`.
    """
    z_R = float(z_R)
    df = pd.DataFrame()
    timedirs = os.listdir("postProcessing/sets")
    latest_time = max(timedirs)
    fname_u = "{}_{}_UPrime2Mean.csv".format(turbine, z_R)
    fname_k = "{}_{}_kMean.csv".format(turbine, z_R)
    dfi = pd.read_csv(os.path.join("postProcessing", "sets", latest_time,
                      fname_u))
    df["y_R"] = dfi.y/R[turbine]
    df["k_resolved"] = 0.5*(dfi.UPrime2Mean_0 + dfi.UPrime2Mean_3
                            + dfi.UPrime2Mean_5)
    try:
        dfi = pd.read_csv(os.path.join("postProcessing", "sets", latest_time,
                          fname_k))
        df["k_modeled"] = dfi.kMean
        df["k_total"] = df.k_modeled + df.k_resolved
    except FileNotFoundError:
        df["k_modeled"] = np.zeros(len(df.y_R))*np.nan
        df["k_total"] = df.k_resolved
    return df


def load_k_map(amount="total"):
    """Load all TKE profiles. Returns a `DataFrame` with `z_H` as the index and
    `y_R` as columns.
    """
    sets_dir = os.path.join("postProcessing", "sets")
    latest_time = max(os.listdir(sets_dir))
    data_dir = os.path.join(sets_dir, latest_time)
    flist = os.listdir(data_dir)
    z_H = []
    for fname in flist:
        if "UPrime2Mean" in fname:
            z_H.append(float(fname.split("_")[1]))
    z_H.sort()
    z_H.reverse()
    k = []
    for z_H_i in z_H:
        dfi = load_k_profile(z_H_i)
        k.append(dfi["k_" + amount].values)
    y_R = dfi.y_R.values
    k = np.array(k).reshape((len(z_H), len(y_R)))
    df = pd.DataFrame(k, index=z_H, columns=y_R)
    return df


def load_upup_profile(turbine="turbine2", z_R=0.0):
    """Load data from the sampled `UPrime2Mean` and `RMeanXX` and
    return it as a pandas `DataFrame`.
    """
    z_R = float(z_R)
    df = pd.DataFrame()
    timedirs = os.listdir("postProcessing/sets")
    latest_time = max(timedirs)
    fname_u = "{}_{}_UPrime2Mean.csv".format(turbine, z_R)
    fname_k = "{}_{}_kMean_RMeanXX.csv".format(turbine, z_R)
    dfi = pd.read_csv(os.path.join("postProcessing", "sets", latest_time,
                      fname_u))
    df["y_R"] = dfi.y/R[turbine]
    df["upup_resolved"] = dfi.UPrime2Mean_0
    dfi = pd.read_csv(os.path.join("postProcessing", "sets", latest_time,
                      fname_k))
    df["upup_modeled"] = dfi.RMeanXX
    df["upup_total"] = df.upup_modeled + df.upup_resolved
    return df


def load_perf(turbine="turbine1", verbose=True):
    """Load turbine performance data."""
    df = pd.read_csv("postProcessing/turbines/0/{}.csv".format(turbine))
    df = df.drop_duplicates("time", keep="last")
    t1 = df.time.iloc[len(df.time)//2]
    if verbose:
        print("{} performance from {:.1f}--{:.1f} seconds:".format(
                turbine, t1, df.time.max()))
        print("Mean TSR = {:.2f}".format(df.tsr[df.time >= t1].mean()))
        print("Mean C_P = {:.2f}".format(df.cp[df.time >= t1].mean()))
        print("Mean C_D = {:.2f}".format(df.cd[df.time >= t1].mean()))
    return df


def calc_perf(t1=1.0):
    """Calculate the performance of both turbines. Return NaN if turbine is
    not active.
    """
    df1 = pd.read_csv("postProcessing/turbines/0/turbine1.csv")
    df2 = pd.read_csv("postProcessing/turbines/0/turbine2.csv")
    df1 = df1.drop_duplicates("time", keep="last")
    df2 = df2.drop_duplicates("time", keep="last")
    df1 = df1[df1.time >= t1]
    df2 = df2[df2.time >= t1]
    return {"tsr_turbine1": df1.tsr.mean(),
            "cp_turbine1": df1.cp.mean(),
            "cd_turbine1": df1.cd.mean(),
            "tsr_turbine2": df2.tsr.mean(),
            "cp_turbine2": df2.cp.mean(),
            "cd_turbine2": df2.cd.mean()}


def load_exp_perf(turbine="turbine1", quantity="cp"):
    """Load experimental performance data from Pierella et al. (2014)"""
    fpath = "processed/Pierella2014/{}_{}.csv".format(turbine, quantity)
    df = pd.read_csv(fpath, skipinitialspace=True)
    # Correct for the fact experimental results use nominal dimensions
    df.tsr *= R[turbine]/R["nominal"]
    df[quantity] *= A["nominal"]/A[turbine]
    return df
