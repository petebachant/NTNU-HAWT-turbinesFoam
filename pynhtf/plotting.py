#!/usr/bin/env python
"""Plotting functions."""

from __future__ import division, print_function
import matplotlib.pyplot as plt
import pandas as pd
from .processing import *

labels = {"meanu" : r"$U/U_\infty$",
          "stdu" : r"$\sigma_u/U_\infty$",
          "meanv" : r"$V/U_\infty$",
          "meanw" : r"$W/U_\infty$",
          "meanuv" : r"$\overline{u'v'}/U_\infty^2$",
          "angle_deg": "Azimuthal angle (degrees)",
          "time": "Time (s)"}


def plot_al_perf(name="blade1", save=False):
    df_turb = pd.read_csv("postProcessing/turbines/0/turbine1.csv")
    df_turb = df_turb.drop_duplicates("time", keep="last")
    df = pd.read_csv(
        "postProcessing/actuatorLines/0/turbine1.{}.csv".format(name)
    )
    df = df.drop_duplicates("time", keep="last")
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
    if save:
        plt.savefig("figures/" + name + "-perf.pdf")


def plot_blade_perf(save=False):
    plot_al_perf("blade1", save=save)


def plot_spanwise(save=False):
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
    if save:
        plt.savefig("figures/spanwise.pdf")


def plot_meancontquiv(turbine="turbine2", save=False):
    mean_u = load_vel_map(turbine=turbine, component="u")
    mean_v = load_vel_map(turbine=turbine, component="v")
    mean_w = load_vel_map(turbine=turbine, component="w")
    y_R = np.round(np.asarray(mean_u.columns.values, dtype=float), decimals=4)
    z_R = np.asarray(mean_u.index.values, dtype=float)
    plt.figure(figsize=(7.5, 4.1))
    # Add contours of mean velocity
    cs = plt.contourf(y_R, z_R, mean_u/U, 20, cmap=plt.cm.coolwarm)
    cb = plt.colorbar(cs, orientation="vertical")
    cb.set_label(r"$U/U_{\infty}$")
    # Make quiver plot of v and w velocities
    Q = plt.quiver(y_R, z_R, mean_v/U, mean_w/U, angles="xy", width=0.0022,
                   edgecolor="none", scale=3.0)
    plt.xlabel(r"$y/R$")
    plt.ylabel(r"$z/R$")
    plt.quiverkey(Q, 0.65, 0.045, 0.1, r"$0.1 U_\infty$",
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
    if save:
        plt.savefig("figures/" + turbine + "-meancontquiv.pdf")


def plot_upup_profile(amount="total", turbine="turbine2", z_R=0.0, ax=None,
                      exp=True, legend=True):
    """Plot the streamwise velocity variance."""
    if ax is None:
        fig, ax = plt.subplots()
    df = load_upup_profile(turbine=turbine, z_R=z_R)
    ax.plot(df.y_R, df["upup_" + amount]/U**2, "-o", label="ALM")
    if exp:
        df_exp = pd.read_csv("processed/Pierella2014/meanupup_xD1.csv",
                             skipinitialspace=True)
        df_exp.y_R *= R["nominal"]/R[turbine]
        ax.plot(df_exp.y_R, df_exp.meanupup_Uinfty2, "^",
                markerfacecolor="none", label="Exp.")
        if legend:
            ax.legend(loc="best")
    ax.set_xlabel("$y/R$")
    ax.set_ylabel(r"$\overline{u^\prime u^\prime}/U_\infty^2$")
    try:
        fig.tight_layout()
    except UnboundLocalError:
        pass


def plot_u_profile(turbine="turbine2", z_R=0.0, ax=None, exp=True, legend=True):
    """Plot mean streamwise velocity."""
    if ax is None:
        fig, ax = plt.subplots()
    df = load_u_profile(turbine=turbine, z_R=z_R)
    ax.plot(df.y_R, df.u/U, "-o", label="ALM")
    if exp:
        df_exp = pd.read_csv("processed/Pierella2014/meanu_xD1.csv",
                             skipinitialspace=True)
        df_exp.y_R *= R["nominal"]/R[turbine]
        ax.plot(df_exp.y_R, df_exp.meanu_Uinfty, "^",
                markerfacecolor="none", label="Exp.")
        if legend:
            ax.legend(loc="best")
    ax.set_xlabel("$y/R$")
    ax.set_ylabel(labels["meanu"])
    try:
        fig.tight_layout()
    except UnboundLocalError:
        pass


def plot_cp(turbine="both", x="time", save=False):
    turbine = str(turbine)
    fig, ax = plt.subplots()
    if turbine == "both" or turbine == "turbine1":
        df1 = load_perf(turbine="turbine1")
        if not np.isnan(df1.cp.mean()):
            ax.plot(df1[x], df1.cp, label="Turbine 1")
    if turbine == "both" or turbine == "turbine2":
        df2 = load_perf(turbine="turbine2")
        if not np.isnan(df2.cp.mean()):
            ax.plot(df2[x], df2.cp, label="Turbine 2")
    ax.set_xlabel(labels[x])
    ax.set_ylabel("$C_P$")
    ax.legend(loc="upper right")
    fig.tight_layout()
    if save:
        fig.savefig("figures/cp-time-series.png", dpi=300)
        fig.savefig("figures/cp-time-series.pdf")


def plot_perf_curves(exp=False, save=False):
    """Plot performance curves."""
    df1 = pd.read_csv("processed/turbine1_tsr_sweep.csv")
    df2 = pd.read_csv("processed/turbine2_tsr_sweep.csv")
    if exp:
        df_exp_turbine1_cp = load_exp_perf("turbine1", "cp")
        df_exp_turbine1_cd = load_exp_perf("turbine1", "cd")
        df_exp_turbine2_cp = load_exp_perf("turbine2", "cp")
        df_exp_turbine2_cd = load_exp_perf("turbine2", "cd")
    fig, ax = plt.subplots(figsize=(7.5, 3.5), nrows=1, ncols=2)
    ax[0].plot(df1.tsr_turbine1, df1.cp_turbine1, "-o", color="b", label="ALM")
    ax[0].plot(df2.tsr_turbine2, df2.cp_turbine2, "-o", color="g", label="")
    ax[0].set_ylabel(r"$C_P$")
    ax[1].plot(df1.tsr_turbine1, df1.cd_turbine1, "-o", color="b", label="ALM")
    ax[1].plot(df2.tsr_turbine2, df2.cd_turbine2, "-o", color="g", label="")
    ax[1].set_ylabel(r"$C_D$")
    for a in ax:
        a.set_xlabel(r"$\lambda$")
    if exp:
        ax[0].plot(df_exp_turbine1_cp.tsr, df_exp_turbine1_cp.cp, "^",
                   label="Exp.")
        ax[1].plot(df_exp_turbine1_cd.tsr, df_exp_turbine1_cd.cd, "^",
                   label="Exp.")
        ax[0].plot(df_exp_turbine2_cp.tsr, df_exp_turbine2_cp.cp, "^", label="")
        ax[1].plot(df_exp_turbine2_cd.tsr, df_exp_turbine2_cd.cd, "^", label="")
        ax[1].legend(loc="lower right")
    ax[1].set_ylim((0, None))
    fig.tight_layout()
    if save:
        figname = "perf-curves"
        plt.savefig("figures/" + figname + ".pdf")
        plt.savefig("figures/" + figname + ".png", dpi=300)


def plot_profiles(save=False):
    """Plot mean and turbulence wake profiles."""
    fig, (ax1, ax2) = plt.subplots(figsize=(7.5, 3.5), nrows=1, ncols=2)
    plot_u_profile(ax=ax1, legend=True)
    plot_upup_profile(ax=ax2, legend=False)
    fig.tight_layout()
    if save:
        figname = "wake-profiles"
        plt.savefig("figures/" + figname + ".pdf")
        plt.savefig("figures/" + figname + ".png", dpi=300)
