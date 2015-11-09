#!/usr/bin/env python
"""
Plotting functions.
"""

from __future__ import division, print_function
import matplotlib.pyplot as plt
import pandas as pd
from .processing import *

ylabels = {"meanu" : r"$U/U_\infty$",
           "stdu" : r"$\sigma_u/U_\infty$",
           "meanv" : r"$V/U_\infty$",
           "meanw" : r"$W/U_\infty$",
           "meanuv" : r"$\overline{u'v'}/U_\infty^2$"}


def plot_al_perf(name="blade1"):
    df_turb = pd.read_csv("postProcessing/turbines/0/turbine.csv")
    df_turb = df_turb.drop_duplicates("time", take_last=True)
    df = pd.read_csv("postProcessing/actuatorLines/0/{}.csv".format(name))
    df = df.drop_duplicates("time", take_last=True)
    df["angle_deg"] = df_turb.angle_deg
    plt.figure()
    plt.plot(df.angle_deg, df.alpha_deg)
    plt.xlabel("Azimuthal angle (degrees)")
    plt.ylabel("Angle of attack (degrees)")
    plt.tight_layout()
    plt.figure()
    plt.plot(df.angle_deg, df.rel_vel_mag)
    plt.xlabel("Azimuthal angle (degrees)")
    plt.ylabel("Relative velocity (m/s)")
    plt.tight_layout()


def plot_blade_perf():
    plot_al_perf("blade1")


def plot_spanwise():
    elements_dir = "postProcessing/actuatorLineElements/0"
    elements = os.listdir(elements_dir)
    dfs = {}
    r_R = np.zeros(len(elements))
    fx = np.zeros(len(elements))
    ft = np.zeros(len(elements))
    for e in elements:
        i = int(e.replace("blade1Element", "").replace(".csv", ""))
        df = pd.read_csv(os.path.join(elements_dir, e))
        r_R[i] = np.sqrt(df.y**2 + df.z**2).iloc[-1]/R
        fx[i] = df.fx.iloc[-1]
        ft[i] = np.sqrt(df.fy**2 + df.fz**2).iloc[-1]
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(7.5, 3.25))
    ax[0].plot(r_R, 2*ft/(U_infty**2*R))
    ax[0].set_ylabel(r"$F_\theta / (\rho R U_\infty^2)$")
    ax[1].plot(r_R, 2*fx/(R*U_infty**2))
    ax[1].set_ylabel(r"$F_x / (\rho R U_\infty^2 )$")
    for a in ax:
        a.set_xlabel("$r/R$")
    fig.tight_layout()


def plot_meancontquiv(turbine="turbine2"):
    mean_u = load_vel_map(turbine=turbine, component="u")
    mean_v = load_vel_map(turbine=turbine, component="v")
    mean_w = load_vel_map(turbine=turbine, component="w")
    y_R = np.round(np.asarray(mean_u.columns.values, dtype=float), decimals=4)
    z_R = np.asarray(mean_u.index.values, dtype=float)
    plt.figure(figsize=(7, 9))
    # Add contours of mean velocity
    cs = plt.contourf(y_R, z_R, mean_u/U, 20, cmap=plt.cm.coolwarm)
    cb = plt.colorbar(cs, shrink=1, extend="both",
                      orientation="horizontal", pad=0.1)
                      #ticks=np.round(np.linspace(0.44, 1.12, 10), decimals=2))
    cb.set_label(r"$U/U_{\infty}$")
    # Make quiver plot of v and w velocities
    Q = plt.quiver(y_R, z_R, mean_v/U, mean_w/U, angles="xy", width=0.0022,
                   edgecolor="none", scale=3.0)
    plt.xlabel(r"$y/R$")
    plt.ylabel(r"$z/R$")
    plt.quiverkey(Q, 0.8, 0.21, 0.1, r"$0.1 U_\infty$",
               labelpos="E",
               coordinates="figure",
               fontproperties={"size": "small"})
    ax = plt.axes()
    ax.set_aspect(1)
    # Plot circle to represent turbine frontal area
    circ = plt.Circle((0, 0), radius=1, facecolor="none", edgecolor="gray",
                      linewidth=3.0)
    ax.add_patch(circ)
    plt.tight_layout()


def plot_cp(angle0=4000.0, turbine="both"):
    turbine = str(turbine)
    fig, ax = plt.subplots()
    if turbine == "both" or turbine == "turbine1":
        df1 = load_perf(turbine="turbine1", angle0=angle0)
        ax.plot(df1.angle_deg, df1.cp, label="Turbine 1")
    if turbine == "both" or turbine == "turbine2":
        df2 = load_perf(turbine="turbine2", angle0=angle0)
        ax.plot(df2.angle_deg, df2.cp, label="Turbine 2")
    ax.set_xlabel("Azimuthal angle (degrees)")
    ax.set_ylabel("$C_P$")
    ax.legend(loc="upper right")
    fig.tight_layout()
