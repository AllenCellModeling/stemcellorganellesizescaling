#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard library
import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pickle


# Third party

# Relative

print("Libraries loaded succesfully")
###############################################################################

log = logging.getLogger(__name__)

###############################################################################


# %% Simple function to load statistics
def loadps(pairstats_root, x):
    with open(pairstats_root / f"{x}.pickle", "rb") as f:
        result = pickle.load(f)
    return result


# %% Flexible scatter plot
def fscatter(
    cellnuc_metrics,
    cellnuc_abbs,
    pairs,
    cells,
    stats_root,
    save_flag,
    pic_root,
    name,
    kde_flag=False,
    fourcolors_flag=False,
    colorpoints_flag=False,
    rollingavg_flag=False,
    ols_flag=False,
    N2=1000,
    plotcells=[]
):

    #%% Selecting number of pairs
    no_of_pairs, _ = pairs.shape
    nrows = np.floor(np.sqrt(2 / 3 * no_of_pairs))
    if nrows == 0:
        nrows = 1
    ncols = np.floor(nrows * 3 / 2)
    while nrows * ncols < no_of_pairs:
        ncols += 1

    #%% Archery new colormap
    white = np.array([1, 1, 1, 1])
    green = np.array([0, 1, 0, 1])
    blue = np.array([0, 0, 1, 1])
    red = np.array([1, 0, 0, 1])
    magenta = np.array([0.5, 0, 0.5, 1])
    black = np.array([0, 0, 0, 1])
    newcolors = np.zeros((100, 4))
    newcolors[0:10, :] = white
    newcolors[10:90, :] = blue
    newcolors[50:90, :] = red
    newcolors[90:100, :] = magenta
    newcmp = ListedColormap(newcolors)

    #%% Spectral
    cpmap = plt.cm.get_cmap(plt.cm.plasma)
    cpmap = cpmap(np.linspace(0, 1, 100) ** 0.4)
    cpmap[0:10, 3] = np.linspace(0.3, 1, 10)
    cpmap = ListedColormap(cpmap)

    #%% Plotting parameters
    fac = 1000
    ms = 0.5
    fs2 = np.round(np.interp(nrows * ncols, [6, 21, 50], [25, 12, 8]))
    fs = np.round(fs2 * 2 / 3)
    lw2 = 2
    nbins = 100
    plt.rcParams.update({"font.size": fs})

    #%% Time for a flexible scatterplot
    w1 = 0.001
    w2 = 0.01
    w3 = 0.001
    h1 = 0.001
    h2 = 0.01
    h3 = 0.001
    xp = 0.1
    yp = 0.1
    xx = (1 - w1 - ((ncols - 1) * w2) - w3) / ncols
    yy = (1 - h1 - ((nrows - 1) * h2) - h3) / nrows
    xw = xx * xp
    xx = xx * (1 - xp)
    yw = yy * yp
    yy = yy * (1 - yp)

    fig = plt.figure(figsize=(16, 9))

    if len(plotcells) > 0:
        plotcells = cells.merge(plotcells, on='CellId', how='inner')

    for i, xy_pair in enumerate(pairs):

        print(i)

        metricX = cellnuc_metrics[xy_pair[0]]
        metricY = cellnuc_metrics[xy_pair[1]]
        abbX = cellnuc_abbs[xy_pair[0]]
        abbY = cellnuc_abbs[xy_pair[1]]

        # data
        x = cells[metricX]
        y = cells[metricY]
        x = x / fac
        y = y / fac
        # x = x.sample(n=1000,random_state=86)
        # y = y.sample(n=1000,random_state=86)

        if len(plotcells) > 0:
            x_pc = plotcells[metricX]
            y_pc = plotcells[metricY]
            x_pc = x_pc / fac
            y_pc = y_pc / fac


        # select subplot
        row = nrows - np.ceil((i + 1) / ncols) + 1
        row = row.astype(np.int64)
        col = (i + 1) % ncols
        if col == 0:
            col = ncols
        col = col.astype(np.int64)
        print(f"{i}_{row}_{col}")

        # Main scatterplot
        ax = fig.add_axes(
            [
                w1 + ((col - 1) * (xw + xx + w2)) + xw,
                h1 + ((row - 1) * (yw + yy + h2)) + yw,
                xx,
                yy,
            ]
        )

        if kde_flag is True:
            xii = loadps(stats_root, f"{metricX}_{metricY}_xii") / fac
            yii = loadps(stats_root, f"{metricX}_{metricY}_yii") / fac
            zii = loadps(stats_root, f"{metricX}_{metricY}_zii")
            cii = loadps(stats_root, f"{metricX}_{metricY}_cell_dens")
            ax.set_ylim(top=np.max(yii))
            ax.set_ylim(bottom=np.min(yii))
            if fourcolors_flag is True:
                ax.pcolormesh(xii, yii, zii, cmap=newcmp)
            elif colorpoints_flag is True:
                sorted_cells = np.argsort(cii)
                cii[sorted_cells] = np.arange(len(sorted_cells))
                ax.scatter(x, y, c=cii, s=ms, cmap=cpmap)
            else:
                ax.pcolormesh(xii, yii, zii, cmap=plt.cm.magma)
                sorted_cells = np.argsort(cii)
                # min_cells = sorted_cells[0:N2]
                # min_cells = min_cells.astype(int)
                # ax.plot(x[min_cells], y[min_cells], 'w.', markersize=ms)
                np.random.shuffle(sorted_cells)
                min_cells = sorted_cells[0:N2]
                min_cells = min_cells.astype(int)
                ax.plot(x[min_cells], y[min_cells], "w.", markersize=ms)
        else:
            ax.plot(x, y, "b.", markersize=ms)

        if len(plotcells) > 0:
            ax.plot(x_pc, y_pc, "rs", markersize=3)

        xticks = ax.get_xticks()
        yticks = ax.get_yticks()
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.grid()
        # ax.text(xlim[0],ylim[1],f"{abbX} vs {abbY}",fontsize=fs2, verticalalignment = 'top')
        if kde_flag is True:
            if (fourcolors_flag is True) or (colorpoints_flag is True):
                ax.text(
                    xlim[1],
                    ylim[1],
                    f"n= {len(x)}",
                    fontsize=fs,
                    verticalalignment="top",
                    horizontalalignment="right",
                    color="black",
                )
            else:
                ax.text(
                    xlim[1],
                    ylim[1],
                    f"n= {len(x)}",
                    fontsize=fs,
                    verticalalignment="top",
                    horizontalalignment="right",
                    color="white",
                )
        else:
            ax.text(
                xlim[1],
                ylim[1],
                f"n= {len(x)}",
                fontsize=fs,
                verticalalignment="top",
                horizontalalignment="right",
            )
        if rollingavg_flag is True:
            rollavg_x = loadps(stats_root, f"{metricX}_{metricY}_x_ra") / fac
            rollavg_y = loadps(stats_root, f"{metricX}_{metricY}_y_ra") / fac
            ax.plot(rollavg_x, rollavg_y[:, 0], "lime", linewidth=lw2)

        if ols_flag is True:
            xii = loadps(stats_root, f"{metricX}_{metricY}_xii") / fac
            pred_yL = loadps(stats_root, f"{metricX}_{metricY}_pred_matL") / fac
            pred_yC = loadps(stats_root, f"{metricX}_{metricY}_pred_matC") / fac
            if kde_flag is True:
                if fourcolors_flag is True:
                    ax.plot(xii, pred_yL, "gray")
                elif colorpoints_flag is True:
                    ax.plot(xii, pred_yL, "gray")
                else:
                    ax.plot(xii, pred_yL, "w")
            else:
                ax.plot(xii, pred_yL, "r")
                ax.plot(xii, pred_yC, "m")

        if ols_flag is True:
            val = loadps(stats_root, f"{metricX}_{metricY}_rs_vecL")
            ci = np.round(np.percentile(val, [2, 98]), 2)
            cim = np.round(np.percentile(val, [50]), 2)
            pc = np.round(np.sqrt(np.percentile(val, [50])), 2)
            val2 = loadps(stats_root, f"{metricX}_{metricY}_rs_vecC")
            ci2 = np.round(np.percentile(val2, [2, 98]), 2)
            pc2 = np.round(np.sqrt(np.percentile(val2, [50])), 2)

            if kde_flag is True:
                if fourcolors_flag is True:
                    plt.text(
                        xlim[0],
                        ylim[1],
                        f"rs={ci[0]}-{ci[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="gray",
                    )
                    plt.text(
                        xlim[0],
                        0.9 * ylim[1],
                        f"pc={pc[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="gray",
                    )
                elif colorpoints_flag is True:
                    plt.text(
                        xlim[0],
                        ylim[1],
                        f"rs={cim[0]}, pc={pc[0]}",
                        fontsize=fs,
                        verticalalignment="top",
                        color="black",
                    )
                else:
                    plt.text(
                        xlim[0],
                        ylim[1],
                        f"rs={ci[0]}-{ci[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="w",
                    )
                    plt.text(
                        xlim[0],
                        0.9 * ylim[1],
                        f"pc={pc[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="w",
                    )
            else:
                plt.text(
                    xlim[0],
                    ylim[1],
                    f"rs={ci[0]}-{ci[1]}",
                    fontsize=fs2 - 2,
                    verticalalignment="top",
                    color="r",
                )
                plt.text(
                    xlim[0],
                    0.9 * ylim[1],
                    f"pc={pc[0]}",
                    fontsize=fs2 - 2,
                    verticalalignment="top",
                    color="r",
                )
                plt.text(
                    xlim[0],
                    0.8 * ylim[1],
                    f"rs={ci2[0]}-{ci2[1]}",
                    fontsize=fs2 - 2,
                    verticalalignment="top",
                    color="m",
                )
                plt.text(
                    xlim[0],
                    0.7 * ylim[1],
                    f"pc={pc2[0]}",
                    fontsize=fs2 - 2,
                    verticalalignment="top",
                    color="m",
                )

        ax.set_xticks(xticks)
        ax.set_yticks(yticks)
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.set_xlim(left=xlim[0], right=xlim[1])
        ax.set_ylim(bottom=ylim[0], top=ylim[1])

        # Bottom histogram
        ax = fig.add_axes(
            [
                w1 + ((col - 1) * (xw + xx + w2)) + xw,
                h1 + ((row - 1) * (yw + yy + h2)),
                xx,
                yw,
            ]
        )
        ax.hist(x, bins=nbins, color=[0.5, 0.5, 0.5, 0.5])
        ylimBH = ax.get_ylim()
        ax.set_xticks(xticks)
        ax.set_yticks([])
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.set_xlim(left=xlim[0], right=xlim[1])
        ax.grid()
        ax.invert_yaxis()
        for n, val in enumerate(xticks):
            if val >= xlim[0] and val <= xlim[1]:
                if int(val) == val:
                    val = int(val)
                else:
                    val = np.round(val, 2)
                if kde_flag is True:
                    if (fourcolors_flag is True) or (colorpoints_flag is True):
                        ax.text(
                            val,
                            ylimBH[0],
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="center",
                            verticalalignment="bottom",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )
                    else:
                        ax.text(
                            val,
                            ylimBH[0],
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="center",
                            verticalalignment="bottom",
                            color=[1, 1, 1, 0.5],
                        )

                else:
                    ax.text(
                        val,
                        ylimBH[0],
                        f"{val}",
                        fontsize=fs,
                        horizontalalignment="center",
                        verticalalignment="bottom",
                        color=[0.5, 0.5, 0.5, 0.5],
                    )

        ax.text(
            np.mean(xlim),
            ylimBH[1],
            f"{abbX}",
            fontsize=fs2,
            horizontalalignment="center",
            verticalalignment="bottom",
        )
        ax.axis("off")

        # Side histogram
        ax = fig.add_axes(
            [
                w1 + ((col - 1) * (xw + xx + w2)),
                h1 + ((row - 1) * (yw + yy + h2)) + yw,
                xw,
                yy,
            ]
        )
        ax.hist(y, bins=nbins, color=[0.5, 0.5, 0.5, 0.5], orientation="horizontal")
        xlimSH = ax.get_xlim()
        ax.set_yticks(yticks)
        ax.set_xticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_ylim(bottom=ylim[0], top=ylim[1])
        ax.grid()
        ax.invert_xaxis()
        for n, val in enumerate(yticks):
            if val >= ylim[0] and val <= ylim[1]:
                if int(val) == val:
                    val = int(val)
                else:
                    val = np.round(val, 2)
                if kde_flag is True:
                    if (fourcolors_flag is True) or (colorpoints_flag is True):
                        ax.text(
                            xlimSH[0],
                            val,
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="left",
                            verticalalignment="center",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )
                    else:
                        ax.text(
                            xlimSH[0],
                            val,
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="left",
                            verticalalignment="center",
                            color=[1, 1, 1, 0.5],
                        )
                else:
                    ax.text(
                        xlimSH[0],
                        val,
                        f"{val}",
                        fontsize=fs,
                        horizontalalignment="left",
                        verticalalignment="center",
                        color=[0.5, 0.5, 0.5, 0.5],
                    )

        ax.text(
            xlimSH[1],
            np.mean(ylim),
            f"{abbY}",
            fontsize=fs2,
            horizontalalignment="left",
            verticalalignment="center",
            rotation=90,
        )
        ax.axis("off")

    if save_flag:
        plot_save_path = pic_root / f"{name}.png"
        plt.savefig(plot_save_path, format="png", dpi=1000)
        plt.close()
    else:
        plt.show()


# %% plot function
def organelle_scatter(
    selected_metrics,
    selected_metrics_abb,
    selected_structures,
    structure_metric,
    cells,
    stats_root,
    save_flag,
    pic_root,
    name,
    kde_flag=False,
    fourcolors_flag=False,
    colorpoints_flag=False,
    rollingavg_flag=False,
    ols_flag=False,
    N2=1000,
    plotcells=[]
):

    #%% Rows and columns
    nrows = len(selected_metrics)
    ncols = len(selected_structures)

    #%% Archery new colormap
    white = np.array([1, 1, 1, 1])
    green = np.array([0, 1, 0, 1])
    blue = np.array([0, 0, 1, 1])
    red = np.array([1, 0, 0, 1])
    magenta = np.array([0.5, 0, 0.5, 1])
    black = np.array([0, 0, 0, 1])
    newcolors = np.zeros((100, 4))
    newcolors[0:10, :] = white
    newcolors[10:90, :] = blue
    newcolors[50:90, :] = red
    newcolors[90:100, :] = magenta
    newcmp = ListedColormap(newcolors)

    #%% Spectral
    cpmap = plt.cm.get_cmap(plt.cm.plasma)
    cpmap = cpmap(np.linspace(0, 1, 100) ** 0.4)
    cpmap[0:10, 3] = np.linspace(0.3, 1, 10)
    cpmap = ListedColormap(cpmap)

    #%% Plotting parameters
    fac = 1000
    ms = 0.5
    fs2 = np.round(np.interp(nrows * ncols, [6, 21, 50], [25, 15, 10]))
    fs = np.round(fs2 * 2 / 3)
    lw2 = 1.5
    nbins = 100
    plt.rcParams.update({"font.size": fs})

    #%% Plotting flags
    # W = 500

    #%% Time for a flexible scatterplot
    w1 = 0.001
    w2 = 0.01
    w3 = 0.001
    h1 = 0.001
    h2 = 0.01
    h3 = 0.001
    xp = 0.1
    yp = 0.1
    xx = (1 - w1 - ((ncols - 1) * w2) - w3) / ncols
    yy = (1 - h1 - ((nrows - 1) * h2) - h3) / nrows
    xw = xx * xp
    xx = xx * (1 - xp)
    yw = yy * yp
    yy = yy * (1 - yp)

    if len(plotcells) > 0:
        plotcells = cells.merge(plotcells, on='CellId', how='inner')

    fig = plt.figure(figsize=(16, 9))

    i = 0

    for yi, metric in enumerate(selected_metrics):
        for xi, struct in enumerate(selected_structures):

            x = cells.loc[cells["structure_name"] == struct, [metric]].squeeze()
            y = cells.loc[
                cells["structure_name"] == struct, [structure_metric]
            ].squeeze()
            # selcel = (cells['structure_name'] == struct).to_numpy()
            # struct_pos = np.argwhere(selcel)
            x = x.to_numpy()
            y = y.to_numpy()
            x = x / fac
            y = y / fac

            if len(plotcells) > 0:
                x_pc = plotcells.loc[plotcells["structure_name"] == struct, [metric]].squeeze().to_numpy()/ fac
                y_pc = plotcells.loc[plotcells["structure_name"] == struct, [structure_metric]].squeeze().to_numpy()/ fac

            metricX = metric
            metricY = struct
            abbX = selected_metrics_abb[yi]
            abbY = selected_structures[xi]

            # select subplot
            i = i + 1
            row = nrows - np.ceil(i / ncols) + 1
            row = row.astype(np.int64)
            col = i % ncols
            if col == 0:
                col = ncols
            print(f"{i}_{row}_{col}")

            # Main scatterplot
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)) + xw,
                    h1 + ((row - 1) * (yw + yy + h2)) + yw,
                    xx,
                    yy,
                ]
            )

            if kde_flag is True:
                xii = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_xii")
                    / fac
                )
                yii = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_yii")
                    / fac
                )
                zii = loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_zii")
                cii = loadps(
                    stats_root, f"{metricX}_{structure_metric}_{metricY}_cell_dens"
                )
                ax.set_ylim(top=np.max(yii))
                ax.set_ylim(bottom=np.min(yii))
                if fourcolors_flag is True:
                    ax.pcolormesh(xii, yii, zii, cmap=newcmp)
                elif colorpoints_flag is True:
                    sorted_cells = np.argsort(cii)
                    cii[sorted_cells] = np.arange(len(sorted_cells))
                    ax.scatter(x, y, c=cii, s=ms, cmap=cpmap)
                else:
                    ax.pcolormesh(xii, yii, zii, cmap=plt.cm.magma)
                    sorted_cells = np.argsort(cii)
                    # min_cells = sorted_cells[0:N2]
                    # min_cells = min_cells.astype(int)
                    # ax.plot(x[min_cells], y[min_cells], 'w.', markersize=ms)
                    np.random.shuffle(sorted_cells)
                    min_cells = sorted_cells[0:N2]
                    min_cells = min_cells.astype(int)
                    ax.plot(x[min_cells], y[min_cells], "w.", markersize=ms)
            else:
                ax.plot(x, y, "b.", markersize=ms)

            if len(plotcells) > 0:
                ax.plot(x_pc, y_pc, "ks", markersize=1)

            xticks = ax.get_xticks()
            yticks = ax.get_yticks()
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.grid()
            # ax.text(xlim[0],ylim[1],f"{abbX} vs {abbY}",fontsize=fs2, verticalalignment = 'top')
            if kde_flag is True:
                if (fourcolors_flag is True) or (colorpoints_flag is True):
                    ax.text(
                        xlim[1],
                        ylim[1],
                        f"n= {len(x)}",
                        fontsize=fs,
                        verticalalignment="top",
                        horizontalalignment="right",
                        color="black",
                    )
                else:
                    ax.text(
                        xlim[1],
                        ylim[1],
                        f"n= {len(x)}",
                        fontsize=fs,
                        verticalalignment="top",
                        horizontalalignment="right",
                        color="white",
                    )

            else:
                ax.text(
                    xlim[1],
                    ylim[1],
                    f"n= {len(x)}",
                    fontsize=fs,
                    verticalalignment="top",
                    horizontalalignment="right",
                )
            if rollingavg_flag is True:
                rollavg_x = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_x_ra")
                    / fac
                )
                rollavg_y = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_y_ra")
                    / fac
                )
                ax.plot(rollavg_x, rollavg_y[:, 0], "lime", linewidth=lw2)

            if ols_flag is True:
                xii = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_xii")
                    / fac
                )
                pred_yL = (
                    loadps(
                        stats_root, f"{metricX}_{structure_metric}_{metricY}_pred_matL"
                    )
                    / fac
                )
                pred_yC = (
                    loadps(
                        stats_root, f"{metricX}_{structure_metric}_{metricY}_pred_matC"
                    )
                    / fac
                )
                if kde_flag is True:
                    if fourcolors_flag is True:
                        ax.plot(xii, pred_yL, "gray")
                    elif colorpoints_flag is True:
                        ax.plot(xii, pred_yL, "gray")
                    else:
                        ax.plot(xii, pred_yL, "w")
                else:
                    ax.plot(xii, pred_yL, "r")
                    ax.plot(xii, pred_yC, "m")

            if ols_flag is True:
                val = loadps(
                    stats_root, f"{metricX}_{structure_metric}_{metricY}_rs_vecL"
                )
                ci = np.round(np.percentile(val, [2, 98]), 2)
                pc = np.round(np.sqrt(np.percentile(val, [50])), 2)
                cim = np.round(np.percentile(val, [50]), 2)
                val2 = loadps(
                    stats_root, f"{metricX}_{structure_metric}_{metricY}_rs_vecC"
                )
                ci2 = np.round(np.percentile(val2, [2, 98]), 2)
                pc2 = np.round(np.sqrt(np.percentile(val2, [50])), 2)

                if kde_flag is True:
                    if fourcolors_flag is True:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={ci[0]}-{ci[1]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="gray",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="gray",
                        )
                    elif colorpoints_flag is True:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={cim[0]}",
                            fontsize=fs,
                            verticalalignment="top",
                            color="black",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs,
                            verticalalignment="top",
                            color="black",
                        )
                    else:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={ci[0]}-{ci[1]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="w",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="w",
                        )
                else:
                    plt.text(
                        xlim[0],
                        ylim[1],
                        f"rs={ci[0]}-{ci[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="r",
                    )
                    plt.text(
                        xlim[0],
                        0.9 * ylim[1],
                        f"pc={pc[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="r",
                    )
                    plt.text(
                        xlim[0],
                        0.8 * ylim[1],
                        f"rs={ci2[0]}-{ci2[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="m",
                    )
                    plt.text(
                        xlim[0],
                        0.7 * ylim[1],
                        f"pc={pc2[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="m",
                    )

            # Bottom histogram
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)) + xw,
                    h1 + ((row - 1) * (yw + yy + h2)),
                    xx,
                    yw,
                ]
            )
            ax.hist(x, bins=nbins, color=[0.5, 0.5, 0.5, 0.5])
            ylimBH = ax.get_ylim()
            ax.set_xticks(xticks)
            ax.set_yticks([])
            ax.set_yticklabels([])
            ax.set_xticklabels([])
            ax.set_xlim(left=xlim[0], right=xlim[1])
            ax.grid()
            ax.invert_yaxis()
            for n, val in enumerate(xticks):
                if val >= xlim[0] and val <= xlim[1]:
                    if int(val) == val:
                        val = int(val)
                    else:
                        val = np.round(val, 2)
                    if kde_flag is True:
                        if (fourcolors_flag is True) or (colorpoints_flag is True):
                            ax.text(
                                val,
                                ylimBH[0],
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="center",
                                verticalalignment="bottom",
                                color=[0.5, 0.5, 0.5, 0.5],
                            )
                        else:
                            ax.text(
                                val,
                                ylimBH[0],
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="center",
                                verticalalignment="bottom",
                                color=[1, 1, 1, 0.5],
                            )

                    else:
                        ax.text(
                            val,
                            ylimBH[0],
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="center",
                            verticalalignment="bottom",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )

            ax.text(
                np.mean(xlim),
                ylimBH[1],
                f"{abbX}",
                fontsize=fs2,
                horizontalalignment="center",
                verticalalignment="bottom",
            )
            ax.axis("off")

            # Side histogram
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)),
                    h1 + ((row - 1) * (yw + yy + h2)) + yw,
                    xw,
                    yy,
                ]
            )
            ax.hist(y, bins=nbins, color=[0.5, 0.5, 0.5, 0.5], orientation="horizontal")
            xlimSH = ax.get_xlim()
            ax.set_yticks(yticks)
            ax.set_xticks([])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_ylim(bottom=ylim[0], top=ylim[1])
            ax.grid()
            ax.invert_xaxis()
            for n, val in enumerate(yticks):
                if val >= ylim[0] and val <= ylim[1]:
                    if int(val) == val:
                        val = int(val)
                    else:
                        val = np.round(val, 2)
                    if kde_flag is True:
                        if (fourcolors_flag is True) or (colorpoints_flag is True):
                            ax.text(
                                xlimSH[0],
                                val,
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="left",
                                verticalalignment="center",
                                color=[0.5, 0.5, 0.5, 0.5],
                            )
                        else:
                            ax.text(
                                xlimSH[0],
                                val,
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="left",
                                verticalalignment="center",
                                color=[1, 1, 1, 0.5],
                            )
                    else:
                        ax.text(
                            xlimSH[0],
                            val,
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="left",
                            verticalalignment="center",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )

            ax.text(
                xlimSH[1],
                np.mean(ylim),
                f"{abbY}",
                fontsize=fs2,
                horizontalalignment="left",
                verticalalignment="center",
                rotation=90,
            )
            ax.axis("off")

    if save_flag:
        plot_save_path = pic_root / f"{name}.png"
        plt.savefig(plot_save_path, format="png", dpi=1000)
        plt.close()
    else:
        plt.show()


# %% plot function
def compensated_scatter(
    selected_metrics,
    selected_metrics_abb,
    selected_structures,
    comp_type,
    lin_type,
    structure_metric,
    cells,
    stats_root,
    save_flag,
    pic_root,
    name,
    kde_flag=False,
    fourcolors_flag=False,
    colorpoints_flag=False,
    rollingavg_flag=False,
    ols_flag=False,
    N2=1000,
):

    #%% Rows and columns
    nrows = len(selected_metrics)
    ncols = len(selected_structures)

    #%% Archery new colormap
    white = np.array([1, 1, 1, 1])
    green = np.array([0, 1, 0, 1])
    blue = np.array([0, 0, 1, 1])
    red = np.array([1, 0, 0, 1])
    magenta = np.array([0.5, 0, 0.5, 1])
    black = np.array([0, 0, 0, 1])
    newcolors = np.zeros((100, 4))
    newcolors[0:10, :] = white
    newcolors[10:90, :] = blue
    newcolors[50:90, :] = red
    newcolors[90:100, :] = magenta
    newcmp = ListedColormap(newcolors)

    #%% Spectral
    cpmap = plt.cm.get_cmap(plt.cm.plasma)
    cpmap = cpmap(np.linspace(0, 1, 100) ** 0.4)
    cpmap[0:10, 3] = np.linspace(0.3, 1, 10)
    cpmap = ListedColormap(cpmap)

    #%% Plotting parameters
    fac = 1000
    ms = 0.5
    fs2 = np.round(np.interp(nrows * ncols, [6, 21, 50], [25, 15, 10]))
    fs = np.round(fs2 * 2 / 3)
    lw2 = 1.5
    nbins = 100
    plt.rcParams.update({"font.size": fs})

    #%% Plotting flags
    # W = 500

    #%% Time for a flexible scatterplot
    w1 = 0.001
    w2 = 0.01
    w3 = 0.001
    h1 = 0.001
    h2 = 0.01
    h3 = 0.001
    xp = 0.1
    yp = 0.1
    xx = (1 - w1 - ((ncols - 1) * w2) - w3) / ncols
    yy = (1 - h1 - ((nrows - 1) * h2) - h3) / nrows
    xw = xx * xp
    xx = xx * (1 - xp)
    yw = yy * yp
    yy = yy * (1 - yp)

    fig = plt.figure(figsize=(16, 9))

    i = 0

    for yi, metric in enumerate(selected_metrics):
        for xi, struct in enumerate(selected_structures):

            if str(metric).startswith("Cell"):
                metric_COMP = f"{metric}_COMP_{lin_type}_nuc_metrics_{comp_type}"
                struct_COMP = (
                    f"{structure_metric}_COMP_{lin_type}_nuc_metrics_{comp_type}"
                )
            elif str(metric).startswith("Nuc"):
                metric_COMP = f"{metric}_COMP_{lin_type}_cell_metrics_{comp_type}"
                struct_COMP = (
                    f"{structure_metric}_COMP_{lin_type}_cell_metrics_{comp_type}"
                )
            else:
                1 / 0

            x = cells.loc[cells["structure_name"] == struct, metric_COMP].squeeze()
            y = cells.loc[cells["structure_name"] == struct, struct_COMP].squeeze()

            # selcel = (cells['structure_name'] == struct).to_numpy()
            # struct_pos = np.argwhere(selcel)
            x = x.to_numpy()
            y = y.to_numpy()
            x = x / fac
            y = y / fac

            metricX = metric
            metricY = struct
            abbX = selected_metrics_abb[yi]
            abbY = selected_structures[xi]

            # select subplot
            i = i + 1
            row = nrows - np.ceil(i / ncols) + 1
            row = row.astype(np.int64)
            col = i % ncols
            if col == 0:
                col = ncols
            print(f"{i}_{row}_{col}")

            # Main scatterplot
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)) + xw,
                    h1 + ((row - 1) * (yw + yy + h2)) + yw,
                    xx,
                    yy,
                ]
            )

            if kde_flag is True:
                xii = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_xii")
                    / fac
                )
                yii = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_yii")
                    / fac
                )
                zii = loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_zii")
                cii = loadps(
                    stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_cell_dens"
                )
                ax.set_ylim(top=np.max(yii))
                ax.set_ylim(bottom=np.min(yii))
                if fourcolors_flag is True:
                    ax.pcolormesh(xii, yii, zii, cmap=newcmp)
                elif colorpoints_flag is True:
                    sorted_cells = np.argsort(cii)
                    cii[sorted_cells] = np.arange(len(sorted_cells))
                    ax.scatter(x, y, c=cii, s=ms, cmap=cpmap)
                else:
                    ax.pcolormesh(xii, yii, zii, cmap=plt.cm.magma)
                    sorted_cells = np.argsort(cii)
                    # min_cells = sorted_cells[0:N2]
                    # min_cells = min_cells.astype(int)
                    # ax.plot(x[min_cells], y[min_cells], 'w.', markersize=ms)
                    np.random.shuffle(sorted_cells)
                    min_cells = sorted_cells[0:N2]
                    min_cells = min_cells.astype(int)
                    ax.plot(x[min_cells], y[min_cells], "w.", markersize=ms)
            else:
                ax.plot(x, y, "b.", markersize=ms)

            xticks = ax.get_xticks()
            yticks = ax.get_yticks()
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.grid()
            # ax.text(xlim[0],ylim[1],f"{abbX} vs {abbY}",fontsize=fs2, verticalalignment = 'top')
            if kde_flag is True:
                if (fourcolors_flag is True) or (colorpoints_flag is True):
                    ax.text(
                        xlim[1],
                        ylim[1],
                        f"n= {len(x)}",
                        fontsize=fs,
                        verticalalignment="top",
                        horizontalalignment="right",
                        color="black",
                    )
                else:
                    ax.text(
                        xlim[1],
                        ylim[1],
                        f"n= {len(x)}",
                        fontsize=fs,
                        verticalalignment="top",
                        horizontalalignment="right",
                        color="white",
                    )

            else:
                ax.text(
                    xlim[1],
                    ylim[1],
                    f"n= {len(x)}",
                    fontsize=fs,
                    verticalalignment="top",
                    horizontalalignment="right",
                )
            if rollingavg_flag is True:
                rollavg_x = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_x_ra")
                    / fac
                )
                rollavg_y = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_y_ra")
                    / fac
                )
                ax.plot(rollavg_x, rollavg_y[:, 0], "lime", linewidth=lw2)

            if ols_flag is True:
                xii = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_xii")
                    / fac
                )
                pred_yL = (
                    loadps(
                        stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_pred_matL"
                    )
                    / fac
                )
                pred_yC = (
                    loadps(
                        stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_pred_matC"
                    )
                    / fac
                )
                if kde_flag is True:
                    if fourcolors_flag is True:
                        ax.plot(xii, pred_yL, "gray")
                    elif colorpoints_flag is True:
                        ax.plot(xii, pred_yL, "gray")
                    else:
                        ax.plot(xii, pred_yL, "w")
                else:
                    ax.plot(xii, pred_yL, "r")
                    ax.plot(xii, pred_yC, "m")

            if ols_flag is True:
                val = loadps(
                    stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_rs_vecL"
                )
                ci = np.round(np.percentile(val, [2, 98]), 2)
                cim = np.round(np.percentile(val, [50]), 2)
                pc = np.round(np.sqrt(np.percentile(val, [50])), 2)
                val2 = loadps(
                    stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_rs_vecC"
                )
                ci2 = np.round(np.percentile(val2, [2, 98]), 2)
                pc2 = np.round(np.sqrt(np.percentile(val2, [50])), 2)

                if kde_flag is True:
                    if fourcolors_flag is True:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={ci[0]}-{ci[1]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="gray",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="gray",
                        )
                    elif colorpoints_flag is True:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={cim[0]}",
                            fontsize=fs,
                            verticalalignment="top",
                            color="black",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs,
                            verticalalignment="top",
                            color="black",
                        )
                    else:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={ci[0]}-{ci[1]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="w",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="w",
                        )
                else:
                    plt.text(
                        xlim[0],
                        ylim[1],
                        f"rs={ci[0]}-{ci[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="r",
                    )
                    plt.text(
                        xlim[0],
                        0.9 * ylim[1],
                        f"pc={pc[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="r",
                    )
                    plt.text(
                        xlim[0],
                        0.8 * ylim[1],
                        f"rs={ci2[0]}-{ci2[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="m",
                    )
                    plt.text(
                        xlim[0],
                        0.7 * ylim[1],
                        f"pc={pc2[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="m",
                    )

            # Bottom histogram
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)) + xw,
                    h1 + ((row - 1) * (yw + yy + h2)),
                    xx,
                    yw,
                ]
            )
            ax.hist(x, bins=nbins, color=[0.5, 0.5, 0.5, 0.5])
            ylimBH = ax.get_ylim()
            ax.set_xticks(xticks)
            ax.set_yticks([])
            ax.set_yticklabels([])
            ax.set_xticklabels([])
            ax.set_xlim(left=xlim[0], right=xlim[1])
            ax.grid()
            ax.invert_yaxis()
            for n, val in enumerate(xticks):
                if val >= xlim[0] and val <= xlim[1]:
                    if int(val) == val:
                        val = int(val)
                    else:
                        val = np.round(val, 2)
                    if kde_flag is True:
                        if (fourcolors_flag is True) or (colorpoints_flag is True):
                            ax.text(
                                val,
                                ylimBH[0],
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="center",
                                verticalalignment="bottom",
                                color=[0.5, 0.5, 0.5, 0.5],
                            )
                        else:
                            ax.text(
                                val,
                                ylimBH[0],
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="center",
                                verticalalignment="bottom",
                                color=[1, 1, 1, 0.5],
                            )

                    else:
                        ax.text(
                            val,
                            ylimBH[0],
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="center",
                            verticalalignment="bottom",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )

            ax.text(
                np.mean(xlim),
                ylimBH[1],
                f"{abbX}",
                fontsize=fs2,
                horizontalalignment="center",
                verticalalignment="bottom",
            )
            ax.axis("off")

            # Side histogram
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)),
                    h1 + ((row - 1) * (yw + yy + h2)) + yw,
                    xw,
                    yy,
                ]
            )
            ax.hist(y, bins=nbins, color=[0.5, 0.5, 0.5, 0.5], orientation="horizontal")
            xlimSH = ax.get_xlim()
            ax.set_yticks(yticks)
            ax.set_xticks([])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_ylim(bottom=ylim[0], top=ylim[1])
            ax.grid()
            ax.invert_xaxis()
            for n, val in enumerate(yticks):
                if val >= ylim[0] and val <= ylim[1]:
                    if int(val) == val:
                        val = int(val)
                    else:
                        val = np.round(val, 2)
                    if kde_flag is True:
                        if (fourcolors_flag is True) or (colorpoints_flag is True):
                            ax.text(
                                xlimSH[0],
                                val,
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="left",
                                verticalalignment="center",
                                color=[0.5, 0.5, 0.5, 0.5],
                            )
                        else:
                            ax.text(
                                xlimSH[0],
                                val,
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="left",
                                verticalalignment="center",
                                color=[1, 1, 1, 0.5],
                            )
                    else:
                        ax.text(
                            xlimSH[0],
                            val,
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="left",
                            verticalalignment="center",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )

            ax.text(
                xlimSH[1],
                np.mean(ylim),
                f"{abbY}",
                fontsize=fs2,
                horizontalalignment="left",
                verticalalignment="center",
                rotation=90,
            )
            ax.axis("off")

    if save_flag:
        plot_save_path = pic_root / f"{name}.png"
        plt.savefig(plot_save_path, format="png", dpi=1000)
        plt.close()
    else:
        plt.show()


# %% plot function
def organelle_scatterT(
    selected_metrics,
    selected_metrics_abb,
    selected_structures,
    structure_metric,
    cells,
    stats_root,
    save_flag,
    pic_root,
    name,
    kde_flag=False,
    fourcolors_flag=False,
    colorpoints_flag=False,
    rollingavg_flag=False,
    ols_flag=False,
    N2=1000,
    plotcells=[]
):

    #%% Rows and columns
    ncols = len(selected_metrics)
    nrows = len(selected_structures)

    #%% Archery new colormap
    white = np.array([1, 1, 1, 1])
    green = np.array([0, 1, 0, 1])
    blue = np.array([0, 0, 1, 1])
    red = np.array([1, 0, 0, 1])
    magenta = np.array([0.5, 0, 0.5, 1])
    black = np.array([0, 0, 0, 1])
    newcolors = np.zeros((100, 4))
    newcolors[0:10, :] = white
    newcolors[10:90, :] = blue
    newcolors[50:90, :] = red
    newcolors[90:100, :] = magenta
    newcmp = ListedColormap(newcolors)

    #%% Spectral
    cpmap = plt.cm.get_cmap(plt.cm.plasma)
    cpmap = cpmap(np.linspace(0, 1, 100) ** 0.4)
    cpmap[0:10, 3] = np.linspace(0.3, 1, 10)
    cpmap = ListedColormap(cpmap)

    #%% Plotting parameters
    fac = 1000
    ms = 0.5
    fs2 = np.round(np.interp(nrows * ncols, [6, 21, 50], [25, 15, 10]))
    fs = np.round(fs2 * 2 / 3)
    lw2 = 1.5
    nbins = 100
    plt.rcParams.update({"font.size": fs})

    #%% Plotting flags
    # W = 500

    #%% Time for a flexible scatterplot
    w1 = 0.001
    w2 = 0.01
    w3 = 0.001
    h1 = 0.001
    h2 = 0.01
    h3 = 0.001
    xp = 0.1
    yp = 0.1
    xx = (1 - w1 - ((ncols - 1) * w2) - w3) / ncols
    yy = (1 - h1 - ((nrows - 1) * h2) - h3) / nrows
    xw = xx * xp
    xx = xx * (1 - xp)
    yw = yy * yp
    yy = yy * (1 - yp)

    if len(plotcells) > 0:
        plotcells = cells.merge(plotcells, on='CellId', how='inner')

    fig = plt.figure(figsize=(16, 9))

    i = 0

    for xi, struct in enumerate(selected_structures):
        for yi, metric in enumerate(selected_metrics):

            x = cells.loc[cells["structure_name"] == struct, [metric]].squeeze()
            y = cells.loc[
                cells["structure_name"] == struct, [structure_metric]
            ].squeeze()
            # selcel = (cells['structure_name'] == struct).to_numpy()
            # struct_pos = np.argwhere(selcel)
            x = x.to_numpy()
            y = y.to_numpy()
            x = x / fac
            y = y / fac

            metricX = metric
            metricY = struct
            abbX = selected_metrics_abb[yi]
            abbY = selected_structures[xi]

            # select subplot
            i = i + 1
            row = nrows - np.ceil(i / ncols) + 1
            row = row.astype(np.int64)
            col = i % ncols
            if col == 0:
                col = ncols
            print(f"{i}_{row}_{col}")

            # Main scatterplot
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)) + xw,
                    h1 + ((row - 1) * (yw + yy + h2)) + yw,
                    xx,
                    yy,
                ]
            )

            if kde_flag is True:
                xii = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_xii")
                    / fac
                )
                yii = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_yii")
                    / fac
                )
                zii = loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_zii")
                cii = loadps(
                    stats_root, f"{metricX}_{structure_metric}_{metricY}_cell_dens"
                )
                ax.set_ylim(top=np.max(yii))
                ax.set_ylim(bottom=np.min(yii))
                if fourcolors_flag is True:
                    ax.pcolormesh(xii, yii, zii, cmap=newcmp)
                elif colorpoints_flag is True:
                    sorted_cells = np.argsort(cii)
                    cii[sorted_cells] = np.arange(len(sorted_cells))
                    ax.scatter(x, y, c=cii, s=ms, cmap=cpmap)
                else:
                    ax.pcolormesh(xii, yii, zii, cmap=plt.cm.magma)
                    sorted_cells = np.argsort(cii)
                    # min_cells = sorted_cells[0:N2]
                    # min_cells = min_cells.astype(int)
                    # ax.plot(x[min_cells], y[min_cells], 'w.', markersize=ms)
                    np.random.shuffle(sorted_cells)
                    min_cells = sorted_cells[0:N2]
                    min_cells = min_cells.astype(int)
                    ax.plot(x[min_cells], y[min_cells], "w.", markersize=ms)
            else:
                ax.plot(x, y, "b.", markersize=ms)

            xticks = ax.get_xticks()
            yticks = ax.get_yticks()
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.grid()
            # ax.text(xlim[0],ylim[1],f"{abbX} vs {abbY}",fontsize=fs2, verticalalignment = 'top')
            if kde_flag is True:
                if (fourcolors_flag is True) or (colorpoints_flag is True):
                    ax.text(
                        xlim[1],
                        ylim[1],
                        f"n= {len(x)}",
                        fontsize=fs,
                        verticalalignment="top",
                        horizontalalignment="right",
                        color="black",
                    )
                else:
                    ax.text(
                        xlim[1],
                        ylim[1],
                        f"n= {len(x)}",
                        fontsize=fs,
                        verticalalignment="top",
                        horizontalalignment="right",
                        color="white",
                    )

            else:
                ax.text(
                    xlim[1],
                    ylim[1],
                    f"n= {len(x)}",
                    fontsize=fs,
                    verticalalignment="top",
                    horizontalalignment="right",
                )
            if rollingavg_flag is True:
                rollavg_x = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_x_ra")
                    / fac
                )
                rollavg_y = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_y_ra")
                    / fac
                )
                ax.plot(rollavg_x, rollavg_y[:, 0], "lime", linewidth=lw2)

            if ols_flag is True:
                xii = (
                    loadps(stats_root, f"{metricX}_{structure_metric}_{metricY}_xii")
                    / fac
                )
                pred_yL = (
                    loadps(
                        stats_root, f"{metricX}_{structure_metric}_{metricY}_pred_matL"
                    )
                    / fac
                )
                pred_yC = (
                    loadps(
                        stats_root, f"{metricX}_{structure_metric}_{metricY}_pred_matC"
                    )
                    / fac
                )
                if kde_flag is True:
                    if fourcolors_flag is True:
                        ax.plot(xii, pred_yL, "gray")
                    elif colorpoints_flag is True:
                        ax.plot(xii, pred_yL, "gray")
                    else:
                        ax.plot(xii, pred_yL, "w")
                else:
                    ax.plot(xii, pred_yL, "r")
                    ax.plot(xii, pred_yC, "m")

            if ols_flag is True:
                val = loadps(
                    stats_root, f"{metricX}_{structure_metric}_{metricY}_rs_vecL"
                )
                ci = np.round(np.percentile(val, [2, 98]), 2)
                pc = np.round(np.sqrt(np.percentile(val, [50])), 2)
                cim = np.round(np.percentile(val, [50]), 2)
                val2 = loadps(
                    stats_root, f"{metricX}_{structure_metric}_{metricY}_rs_vecC"
                )
                ci2 = np.round(np.percentile(val2, [2, 98]), 2)
                pc2 = np.round(np.sqrt(np.percentile(val2, [50])), 2)

                if kde_flag is True:
                    if fourcolors_flag is True:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={ci[0]}-{ci[1]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="gray",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="gray",
                        )
                    elif colorpoints_flag is True:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={cim[0]}",
                            fontsize=fs,
                            verticalalignment="top",
                            color="black",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs,
                            verticalalignment="top",
                            color="black",
                        )
                    else:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={ci[0]}-{ci[1]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="w",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="w",
                        )
                else:
                    plt.text(
                        xlim[0],
                        ylim[1],
                        f"rs={ci[0]}-{ci[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="r",
                    )
                    plt.text(
                        xlim[0],
                        0.9 * ylim[1],
                        f"pc={pc[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="r",
                    )
                    plt.text(
                        xlim[0],
                        0.8 * ylim[1],
                        f"rs={ci2[0]}-{ci2[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="m",
                    )
                    plt.text(
                        xlim[0],
                        0.7 * ylim[1],
                        f"pc={pc2[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="m",
                    )

            # Bottom histogram
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)) + xw,
                    h1 + ((row - 1) * (yw + yy + h2)),
                    xx,
                    yw,
                ]
            )
            ax.hist(x, bins=nbins, color=[0.5, 0.5, 0.5, 0.5])
            ylimBH = ax.get_ylim()
            ax.set_xticks(xticks)
            ax.set_yticks([])
            ax.set_yticklabels([])
            ax.set_xticklabels([])
            ax.set_xlim(left=xlim[0], right=xlim[1])
            ax.grid()
            ax.invert_yaxis()
            for n, val in enumerate(xticks):
                if val >= xlim[0] and val <= xlim[1]:
                    if int(val) == val:
                        val = int(val)
                    else:
                        val = np.round(val, 2)
                    if kde_flag is True:
                        if (fourcolors_flag is True) or (colorpoints_flag is True):
                            ax.text(
                                val,
                                ylimBH[0],
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="center",
                                verticalalignment="bottom",
                                color=[0.5, 0.5, 0.5, 0.5],
                            )
                        else:
                            ax.text(
                                val,
                                ylimBH[0],
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="center",
                                verticalalignment="bottom",
                                color=[1, 1, 1, 0.5],
                            )

                    else:
                        ax.text(
                            val,
                            ylimBH[0],
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="center",
                            verticalalignment="bottom",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )

            ax.text(
                np.mean(xlim),
                ylimBH[1],
                f"{abbX}",
                fontsize=fs2,
                horizontalalignment="center",
                verticalalignment="bottom",
            )
            ax.axis("off")

            # Side histogram
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)),
                    h1 + ((row - 1) * (yw + yy + h2)) + yw,
                    xw,
                    yy,
                ]
            )
            ax.hist(y, bins=nbins, color=[0.5, 0.5, 0.5, 0.5], orientation="horizontal")
            xlimSH = ax.get_xlim()
            ax.set_yticks(yticks)
            ax.set_xticks([])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_ylim(bottom=ylim[0], top=ylim[1])
            ax.grid()
            ax.invert_xaxis()
            for n, val in enumerate(yticks):
                if val >= ylim[0] and val <= ylim[1]:
                    if int(val) == val:
                        val = int(val)
                    else:
                        val = np.round(val, 2)
                    if kde_flag is True:
                        if (fourcolors_flag is True) or (colorpoints_flag is True):
                            ax.text(
                                xlimSH[0],
                                val,
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="left",
                                verticalalignment="center",
                                color=[0.5, 0.5, 0.5, 0.5],
                            )
                        else:
                            ax.text(
                                xlimSH[0],
                                val,
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="left",
                                verticalalignment="center",
                                color=[1, 1, 1, 0.5],
                            )
                    else:
                        ax.text(
                            xlimSH[0],
                            val,
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="left",
                            verticalalignment="center",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )

            ax.text(
                xlimSH[1],
                np.mean(ylim),
                f"{abbY}",
                fontsize=fs2,
                horizontalalignment="left",
                verticalalignment="center",
                rotation=90,
            )
            ax.axis("off")

    if save_flag:
        plot_save_path = pic_root / f"{name}.png"
        plt.savefig(plot_save_path, format="png", dpi=1000)
        plt.close()
    else:
        plt.show()


# %% plot function
def compensated_scatter_t(
    selected_metrics,
    selected_metrics_abb,
    selected_structures,
    comp_type,
    lin_type,
    structure_metric,
    cells,
    stats_root,
    save_flag,
    pic_root,
    name,
    kde_flag=False,
    fourcolors_flag=False,
    colorpoints_flag=False,
    rollingavg_flag=False,
    ols_flag=False,
    N2=1000,
):

    #%% Rows and columns
    ncols = len(selected_metrics)
    nrows = len(selected_structures)

    #%% Archery new colormap
    white = np.array([1, 1, 1, 1])
    green = np.array([0, 1, 0, 1])
    blue = np.array([0, 0, 1, 1])
    red = np.array([1, 0, 0, 1])
    magenta = np.array([0.5, 0, 0.5, 1])
    black = np.array([0, 0, 0, 1])
    newcolors = np.zeros((100, 4))
    newcolors[0:10, :] = white
    newcolors[10:90, :] = blue
    newcolors[50:90, :] = red
    newcolors[90:100, :] = magenta
    newcmp = ListedColormap(newcolors)

    #%% Spectral
    cpmap = plt.cm.get_cmap(plt.cm.plasma)
    cpmap = cpmap(np.linspace(0, 1, 100) ** 0.4)
    cpmap[0:10, 3] = np.linspace(0.3, 1, 10)
    cpmap = ListedColormap(cpmap)

    #%% Plotting parameters
    fac = 1000
    ms = 0.5
    fs2 = np.round(np.interp(nrows * ncols, [6, 21, 50], [25, 15, 10]))
    fs = np.round(fs2 * 2 / 3)
    lw2 = 1.5
    nbins = 100
    plt.rcParams.update({"font.size": fs})

    #%% Plotting flags
    # W = 500

    #%% Time for a flexible scatterplot
    w1 = 0.001
    w2 = 0.01
    w3 = 0.001
    h1 = 0.001
    h2 = 0.01
    h3 = 0.001
    xp = 0.1
    yp = 0.1
    xx = (1 - w1 - ((ncols - 1) * w2) - w3) / ncols
    yy = (1 - h1 - ((nrows - 1) * h2) - h3) / nrows
    xw = xx * xp
    xx = xx * (1 - xp)
    yw = yy * yp
    yy = yy * (1 - yp)

    fig = plt.figure(figsize=(16, 9))

    i = 0

    for xi, struct in enumerate(selected_structures):
        for yi, metric in enumerate(selected_metrics):

            if str(metric).startswith("Cell"):
                metric_COMP = f"{metric}_COMP_{lin_type}_nuc_metrics_{comp_type}"
                struct_COMP = (
                    f"{structure_metric}_COMP_{lin_type}_nuc_metrics_{comp_type}"
                )
            elif str(metric).startswith("Nuc"):
                metric_COMP = f"{metric}_COMP_{lin_type}_cell_metrics_{comp_type}"
                struct_COMP = (
                    f"{structure_metric}_COMP_{lin_type}_cell_metrics_{comp_type}"
                )
            else:
                1 / 0

            x = cells.loc[cells["structure_name"] == struct, metric_COMP].squeeze()
            y = cells.loc[cells["structure_name"] == struct, struct_COMP].squeeze()

            # selcel = (cells['structure_name'] == struct).to_numpy()
            # struct_pos = np.argwhere(selcel)
            x = x.to_numpy()
            y = y.to_numpy()
            x = x / fac
            y = y / fac

            metricX = metric
            metricY = struct
            abbX = selected_metrics_abb[yi]
            abbY = selected_structures[xi]

            # select subplot
            i = i + 1
            row = nrows - np.ceil(i / ncols) + 1
            row = row.astype(np.int64)
            col = i % ncols
            if col == 0:
                col = ncols
            print(f"{i}_{row}_{col}")

            # Main scatterplot
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)) + xw,
                    h1 + ((row - 1) * (yw + yy + h2)) + yw,
                    xx,
                    yy,
                ]
            )

            if kde_flag is True:
                xii = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_xii")
                    / fac
                )
                yii = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_yii")
                    / fac
                )
                zii = loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_zii")
                cii = loadps(
                    stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_cell_dens"
                )
                ax.set_ylim(top=np.max(yii))
                ax.set_ylim(bottom=np.min(yii))
                if fourcolors_flag is True:
                    ax.pcolormesh(xii, yii, zii, cmap=newcmp)
                elif colorpoints_flag is True:
                    sorted_cells = np.argsort(cii)
                    cii[sorted_cells] = np.arange(len(sorted_cells))
                    ax.scatter(x, y, c=cii, s=ms, cmap=cpmap)
                else:
                    ax.pcolormesh(xii, yii, zii, cmap=plt.cm.magma)
                    sorted_cells = np.argsort(cii)
                    # min_cells = sorted_cells[0:N2]
                    # min_cells = min_cells.astype(int)
                    # ax.plot(x[min_cells], y[min_cells], 'w.', markersize=ms)
                    np.random.shuffle(sorted_cells)
                    min_cells = sorted_cells[0:N2]
                    min_cells = min_cells.astype(int)
                    ax.plot(x[min_cells], y[min_cells], "w.", markersize=ms)
            else:
                ax.plot(x, y, "b.", markersize=ms)

            xticks = ax.get_xticks()
            yticks = ax.get_yticks()
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.grid()
            # ax.text(xlim[0],ylim[1],f"{abbX} vs {abbY}",fontsize=fs2, verticalalignment = 'top')
            if kde_flag is True:
                if (fourcolors_flag is True) or (colorpoints_flag is True):
                    ax.text(
                        xlim[1],
                        ylim[1],
                        f"n= {len(x)}",
                        fontsize=fs,
                        verticalalignment="top",
                        horizontalalignment="right",
                        color="black",
                    )
                else:
                    ax.text(
                        xlim[1],
                        ylim[1],
                        f"n= {len(x)}",
                        fontsize=fs,
                        verticalalignment="top",
                        horizontalalignment="right",
                        color="white",
                    )

            else:
                ax.text(
                    xlim[1],
                    ylim[1],
                    f"n= {len(x)}",
                    fontsize=fs,
                    verticalalignment="top",
                    horizontalalignment="right",
                )
            if rollingavg_flag is True:
                rollavg_x = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_x_ra")
                    / fac
                )
                rollavg_y = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_y_ra")
                    / fac
                )
                ax.plot(rollavg_x, rollavg_y[:, 0], "lime", linewidth=lw2)

            if ols_flag is True:
                xii = (
                    loadps(stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_xii")
                    / fac
                )
                pred_yL = (
                    loadps(
                        stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_pred_matL"
                    )
                    / fac
                )
                pred_yC = (
                    loadps(
                        stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_pred_matC"
                    )
                    / fac
                )
                if kde_flag is True:
                    if fourcolors_flag is True:
                        ax.plot(xii, pred_yL, "gray")
                    elif colorpoints_flag is True:
                        ax.plot(xii, pred_yL, "gray")
                    else:
                        ax.plot(xii, pred_yL, "w")
                else:
                    ax.plot(xii, pred_yL, "r")
                    ax.plot(xii, pred_yC, "m")

            if ols_flag is True:
                val = loadps(
                    stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_rs_vecL"
                )
                ci = np.round(np.percentile(val, [2, 98]), 2)
                cim = np.round(np.percentile(val, [50]), 2)
                pc = np.round(np.sqrt(np.percentile(val, [50])), 2)
                val2 = loadps(
                    stats_root, f"{metric_COMP}_{struct_COMP}_{struct}_rs_vecC"
                )
                ci2 = np.round(np.percentile(val2, [2, 98]), 2)
                pc2 = np.round(np.sqrt(np.percentile(val2, [50])), 2)

                if kde_flag is True:
                    if fourcolors_flag is True:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={ci[0]}-{ci[1]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="gray",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="gray",
                        )
                    elif colorpoints_flag is True:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={cim[0]}",
                            fontsize=fs,
                            verticalalignment="top",
                            color="black",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs,
                            verticalalignment="top",
                            color="black",
                        )
                    else:
                        plt.text(
                            xlim[0],
                            ylim[1],
                            f"rs={ci[0]}-{ci[1]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="w",
                        )
                        plt.text(
                            xlim[0],
                            0.9 * ylim[1],
                            f"pc={pc[0]}",
                            fontsize=fs2 - 2,
                            verticalalignment="top",
                            color="w",
                        )
                else:
                    plt.text(
                        xlim[0],
                        ylim[1],
                        f"rs={ci[0]}-{ci[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="r",
                    )
                    plt.text(
                        xlim[0],
                        0.9 * ylim[1],
                        f"pc={pc[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="r",
                    )
                    plt.text(
                        xlim[0],
                        0.8 * ylim[1],
                        f"rs={ci2[0]}-{ci2[1]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="m",
                    )
                    plt.text(
                        xlim[0],
                        0.7 * ylim[1],
                        f"pc={pc2[0]}",
                        fontsize=fs2 - 2,
                        verticalalignment="top",
                        color="m",
                    )

            # Bottom histogram
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)) + xw,
                    h1 + ((row - 1) * (yw + yy + h2)),
                    xx,
                    yw,
                ]
            )
            ax.hist(x, bins=nbins, color=[0.5, 0.5, 0.5, 0.5])
            ylimBH = ax.get_ylim()
            ax.set_xticks(xticks)
            ax.set_yticks([])
            ax.set_yticklabels([])
            ax.set_xticklabels([])
            ax.set_xlim(left=xlim[0], right=xlim[1])
            ax.grid()
            ax.invert_yaxis()
            for n, val in enumerate(xticks):
                if val >= xlim[0] and val <= xlim[1]:
                    if int(val) == val:
                        val = int(val)
                    else:
                        val = np.round(val, 2)
                    if kde_flag is True:
                        if (fourcolors_flag is True) or (colorpoints_flag is True):
                            ax.text(
                                val,
                                ylimBH[0],
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="center",
                                verticalalignment="bottom",
                                color=[0.5, 0.5, 0.5, 0.5],
                            )
                        else:
                            ax.text(
                                val,
                                ylimBH[0],
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="center",
                                verticalalignment="bottom",
                                color=[1, 1, 1, 0.5],
                            )

                    else:
                        ax.text(
                            val,
                            ylimBH[0],
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="center",
                            verticalalignment="bottom",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )

            ax.text(
                np.mean(xlim),
                ylimBH[1],
                f"{abbX}",
                fontsize=fs2,
                horizontalalignment="center",
                verticalalignment="bottom",
            )
            ax.axis("off")

            # Side histogram
            ax = fig.add_axes(
                [
                    w1 + ((col - 1) * (xw + xx + w2)),
                    h1 + ((row - 1) * (yw + yy + h2)) + yw,
                    xw,
                    yy,
                ]
            )
            ax.hist(y, bins=nbins, color=[0.5, 0.5, 0.5, 0.5], orientation="horizontal")
            xlimSH = ax.get_xlim()
            ax.set_yticks(yticks)
            ax.set_xticks([])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_ylim(bottom=ylim[0], top=ylim[1])
            ax.grid()
            ax.invert_xaxis()
            for n, val in enumerate(yticks):
                if val >= ylim[0] and val <= ylim[1]:
                    if int(val) == val:
                        val = int(val)
                    else:
                        val = np.round(val, 2)
                    if kde_flag is True:
                        if (fourcolors_flag is True) or (colorpoints_flag is True):
                            ax.text(
                                xlimSH[0],
                                val,
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="left",
                                verticalalignment="center",
                                color=[0.5, 0.5, 0.5, 0.5],
                            )
                        else:
                            ax.text(
                                xlimSH[0],
                                val,
                                f"{val}",
                                fontsize=fs,
                                horizontalalignment="left",
                                verticalalignment="center",
                                color=[1, 1, 1, 0.5],
                            )
                    else:
                        ax.text(
                            xlimSH[0],
                            val,
                            f"{val}",
                            fontsize=fs,
                            horizontalalignment="left",
                            verticalalignment="center",
                            color=[0.5, 0.5, 0.5, 0.5],
                        )

            ax.text(
                xlimSH[1],
                np.mean(ylim),
                f"{abbY}",
                fontsize=fs2,
                horizontalalignment="left",
                verticalalignment="center",
                rotation=90,
            )
            ax.axis("off")

    if save_flag:
        plot_save_path = pic_root / f"{name}.png"
        plt.savefig(plot_save_path, format="png", dpi=1000)
        plt.close()
    else:
        plt.show()
