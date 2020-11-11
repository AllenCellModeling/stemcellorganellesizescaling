#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard library
import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import statsmodels.api as sm
from sklearn.utils import resample
import datetime
from scipy.stats import gaussian_kde
from matplotlib.colors import ListedColormap
from tqdm import tqdm
from matplotlib import cm
import pickle
import seaborn as sns
import os, platform
import sys, importlib

# Third party

# Relative
from stemcellorganellesizescaling.analyses.utils.scatter_plotting_func import ascatter

importlib.reload(
    sys.modules["stemcellorganellesizescaling.analyses.utils.scatter_plotting_func"]
)
from stemcellorganellesizescaling.analyses.utils.scatter_plotting_func import ascatter

print("Libraries loaded succesfully")
###############################################################################

log = logging.getLogger(__name__)

###############################################################################
#%% Directories
if platform.system() == "Windows":
    data_root = Path("E:/DA/Data/scoss/Data/Nov2020/")
    pic_root = Path("E:/DA/Data/scoss/Pics/Nov2020/")
elif platform.system() == "Linux":
    data_root = Path("/allen/aics/modeling/theok/Projects/Data/scoss/Data/")
    pic_root = Path("/allen/aics/modeling/theok/Projects/Data/scoss/Pics/")
dirs = []
dirs.append(data_root)
dirs.append(pic_root)

save_flag = 0
plt.rcParams.update({"font.size": 8})

# %% Start

# Resolve directories
data_root = dirs[0]
pic_root = dirs[1]

tableIN = "SizeScaling_20201102.csv"
table_compIN = "SizeScaling_20201102_comp.csv"
statsIN = "Stats_20201102"
# Load dataset
cells = pd.read_csv(data_root / tableIN)
print(np.any(cells.isnull()))
cells_COMP = pd.read_csv(data_root / table_compIN)
print(np.any(cells_COMP.isnull()))
structures = pd.read_csv(data_root / 'annotation' / "structure_annotated_20201019.csv")
Grow = pd.read_csv(data_root / 'growing' / "Growthstats_20201102.csv")
print(np.any(cells_COMP.isnull()))

# %% Simple function to load statistics
def loadps(pairstats_root, x):
    with open(pairstats_root / f"{x}.pickle", "rb") as f:
        result = pickle.load(f)
    return result

# %% Feature sets
FS = {}
FS["cellnuc_metrics"] = [
    "Cell surface area",
    "Cell volume",
    "Cell height",
    "Nuclear surface area",
    "Nuclear volume",
    "Nucleus height",
    "Cytoplasmic volume",
]
FS["cellnuc_abbs"] = [
    "Cell area",
    "Cell vol",
    "Cell height",
    "Nuclear area",
    "Nuclear vol",
    "Nucleus height",
    "Cyto vol",
]
FS["cellnuc_COMP_metrics"] = [
    "Cell surface area",
    "Cell volume",
    "Cell height",
    "Nuclear surface area",
    "Nuclear volume",
    "Nucleus height",
]

FS["cellnuc_COMP_abbs"] = [
    "Cell area *N",
    "Cell vol *N",
    "Cell height *N",
    "Nuclear area *C",
    "Nuclear vol *C",
    "Nucleus height *C",
]

FS["struct_metrics"] = ["Structure volume", "Number of pieces"]
FS["COMP_types"] = ["AVH","AV","H"]

# %% Start dataframe
CellNucGrow = pd.DataFrame()
CellNucGrow['cellnuc_name'] = FS["cellnuc_metrics"]
for i, col in enumerate(FS["cellnuc_metrics"]):
    CellNucGrow[col] = np.nan

# %% Part 1 pairwise stats cell and nucleus measurement
print('Cell and nucleus metrics')
ps = (data_root / statsIN / 'cell_nuc_metrics')
for xi, xlabel in enumerate(FS['cellnuc_metrics']):
    for yi, ylabel in enumerate(FS['cellnuc_metrics']):
        if xlabel is not ylabel:
            print(f"{xlabel} vs {ylabel}")
            val = loadps(ps, f"{xlabel}_{ylabel}_rs_vecL")
            pred_yL = loadps(ps, f"{xlabel}_{ylabel}_pred_matL")
            cmin = np.round(100*np.percentile(val,[50]))
            if pred_yL[0] > pred_yL[-1]:
                cmin = -cmin
            CellNucGrow.loc[CellNucGrow['cellnuc_name']==xlabel,ylabel] = cmin

# %% Start dataframe
StructGrow = pd.DataFrame()
StructGrow['structure_name'] = cells['structure_name'].unique()

# %% Part 2 pairwise stats cell and nucleus measurement
print('Cell and nucleus metrics vs structure metrics')
ps = (data_root / statsIN / 'cellnuc_struct_metrics')
for xi, xlabel in enumerate(FS['cellnuc_metrics']):
    for yi, ylabel in enumerate(FS['struct_metrics']):
        print(f"{xlabel} vs {ylabel}")
        selected_structures = cells["structure_name"].unique()
        StructGrow[f"{xlabel}_{ylabel}"] = np.nan
        StructGrow[f"{xlabel}_{ylabel}_min"] = np.nan
        StructGrow[f"{xlabel}_{ylabel}_max"] = np.nan
        for si, struct in enumerate(selected_structures):
            val = loadps(ps, f"{xlabel}_{ylabel}_{struct}_rs_vecL")
            pred_yL = loadps(ps, f"{xlabel}_{ylabel}_{struct}_pred_matL")
            cmin = np.round(100 * np.percentile(val, [50]))
            cmin_min = np.round(100 * np.percentile(val, [5]))
            cmin_max = np.round(100 * np.percentile(val, [95]))
            if pred_yL[0] > pred_yL[-1]:
                cmin = -cmin
                cmin_min = -cmin_min
                cmin_max = -cmin_max
            StructGrow.loc[StructGrow['structure_name'] == struct, f"{xlabel}_{ylabel}"] = cmin
            StructGrow.loc[StructGrow['structure_name'] == struct, f"{xlabel}_{ylabel}_min"] = cmin_min
            StructGrow.loc[StructGrow['structure_name'] == struct, f"{xlabel}_{ylabel}_max"] = cmin_max

ps = (data_root / statsIN / 'cellnuc_struct_COMP_metrics')
comp_columns = list(cells_COMP.columns)
for xi, xlabel in enumerate(
    ['nuc_metrics_AVH', 'nuc_metrics_AV', 'nuc_metrics_H', 'cell_metrics_AVH', 'cell_metrics_AV',
     'cell_metrics_H']):
    for zi, zlabel in enumerate(FS['cellnuc_metrics']):
        for ti, type in enumerate(["Linear", "Complex"]):
            col2 = f"{zlabel}_COMP_{type}_{xlabel}"
            if col2 in comp_columns:
                print(col2)
                for yi, ylabel in enumerate(FS['struct_metrics']):
                    selected_structures = cells_COMP["structure_name"].unique()
                    col1 = f"{ylabel}_COMP_{type}_{xlabel}"
                    StructGrow[f"{zlabel}_{col1}"] = np.nan
                    for si, struct in enumerate(selected_structures):
                        val = loadps(ps, f"{col2}_{col1}_{struct}_rs_vecL")
                        pred_yL = loadps(ps, f"{col2}_{col1}_{struct}_pred_matL")
                        cmin = np.round(100 * np.percentile(val, [50]))
                        if pred_yL[0] > pred_yL[-1]:
                            cmin = -cmin
                        StructGrow.loc[StructGrow['structure_name'] == struct, f"{zlabel}_{col1}"] = cmin

# %% Select columns for heatmap
HM = {}
HM["cellnuc_heatmap"] = [
    "Cell volume",
    "Cell surface area",
    "Nuclear volume",
    "Nuclear surface area",
    "Cytoplasmic volume",
]
HM["cellnuc_heatmap_abbs"] = [
    "Cell vol",
    "Cell area",
    "Nuc vol",
    "Nuc area",
    "Cyto vol",
]
HM["cellnuc_heatmap_COMP_metrics"] = [
    "Cell volume",
    "Cell surface area",
    "Nuclear volume",
    "Nuclear surface area",
]

HM["cellnuc_COMP_abbs"] = [
    "Cell vol*N",
    "Cell area*N",
    "Nuc vol*C",
    "Nuc area*C",
]

HM["struct_heatmap_metrics"] = "Structure volume"
HM["COMP_type"] = "AV"
HM["LIN_type"] = "Linear"

# %% Make heatmap by selecting columns
keepcolumns = ['structure_name']
keepcolumns_min = ['structure_name']
keepcolumns_max = ['structure_name']
for xi, xlabel in enumerate(HM['cellnuc_heatmap']):
    struct_metric = HM["struct_heatmap_metrics"]
    keepcolumns.append(f"{xlabel}_{struct_metric}")
    keepcolumns_min.append(f"{xlabel}_{struct_metric}_min")
    keepcolumns_max.append(f"{xlabel}_{struct_metric}_max")

HeatMap = StructGrow[keepcolumns]
HeatMap_min = StructGrow[keepcolumns_min]
HeatMap_max = StructGrow[keepcolumns_max]

keepcolumns = ['structure_name']
for xi, xlabel in enumerate(HM['cellnuc_heatmap_COMP_metrics']):
    struct_metric = HM["struct_heatmap_metrics"]
    lin_type = HM["LIN_type"]
    comp_type = HM["COMP_type"]
    if str(xlabel).startswith('Cell'):
        keepcolumns.append(f"{xlabel}_{struct_metric}_COMP_{lin_type}_nuc_metrics_{comp_type}")
    elif str(xlabel).startswith('Nuc'):
        keepcolumns.append(f"{xlabel}_{struct_metric}_COMP_{lin_type}_cell_metrics_{comp_type}")
    else:
        1/0

HeatMapComp = StructGrow[keepcolumns]

# %% Annotation
ann_st = structures[[ 'Structure', 'Group', 'Gene']].astype('category')
cat_columns = ann_st.select_dtypes(['category']).columns
num_st = pd.DataFrame()
num_st[cat_columns] = ann_st[cat_columns].apply(lambda x: x.cat.codes)
num_st[['Gene', 'Group', 'Structure']] = np.nan
ann_st = ann_st.to_numpy()
color_st = structures[['Color']]

#%% Plot Arrays
plot_array = HeatMap
plot_array = plot_array.set_index(plot_array['structure_name'],drop=True)
plot_array = plot_array.drop(['structure_name'],axis=1)
plot_array = plot_array.reindex(list(ann_st[:,-1]))
pan = plot_array.to_numpy()

plot_array_min = HeatMap_min
plot_array_min = plot_array_min.set_index(plot_array_min['structure_name'],drop=True)
plot_array_min = plot_array_min.drop(['structure_name'],axis=1)
plot_array_min = plot_array_min.reindex(list(ann_st[:,-1]))
pan_min = plot_array_min.to_numpy()

plot_array_max = HeatMap_max
plot_array_max = plot_array_max.set_index(plot_array_max['structure_name'],drop=True)
plot_array_max = plot_array_max.drop(['structure_name'],axis=1)
plot_array_max = plot_array_max.reindex(list(ann_st[:,-1]))
pan_max = plot_array_max.to_numpy()

plot_arrayComp = HeatMapComp
plot_arrayComp = plot_arrayComp.set_index(plot_arrayComp['structure_name'],drop=True)
plot_arrayComp = plot_arrayComp.drop(['structure_name'],axis=1)
plot_arrayComp = plot_arrayComp.reindex(list(ann_st[:,-1]))
panComp = plot_arrayComp.to_numpy()
panCompC = panComp[:,[0, 1]]
panCompN = panComp[:,[2, 3]]
plot_arrayCompC = plot_arrayComp.iloc[:,[0,1]]
plot_arrayCompN = plot_arrayComp.iloc[:,[2,3]]

plot_arrayCN = CellNucGrow
plot_arrayCN = plot_arrayCN.set_index(plot_arrayCN['cellnuc_name'],drop=True)
plot_arrayCN = plot_arrayCN.drop(['cellnuc_name'],axis=1)
plot_arrayCN = plot_arrayCN.reindex(HM["cellnuc_heatmap"])
plot_arrayCN = plot_arrayCN[HM["cellnuc_heatmap"]]
panCN = plot_arrayCN.to_numpy()
for i in np.arange(panCN.shape[0]):
    for j in np.arange(panCN.shape[1]):
        if i==j:
            panCN[i,j] = 100
        if i<j:
            panCN[i, j] = 0

# %% Pull in Grow numbers
struct_metric = HM["struct_heatmap_metrics"]
growvec = np.zeros((pan.shape[0], 3))
for i, struct in enumerate(list(ann_st[:,-1])):
    growvec[i,0] = Grow.loc[50, f"{struct_metric}_{struct}_50"]
    growvec[i, 1] = Grow.loc[51, f"{struct_metric}_{struct}_25"]
    growvec[i, 2] = Grow.loc[51, f"{struct_metric}_{struct}_75"]

growvecC = np.zeros((len(HM["cellnuc_heatmap"]), 1))
for i, struct in enumerate(HM["cellnuc_heatmap"]):
    growvecC[i] = Grow.loc[50, f"{struct}_50"]
growvecC[0]=100

# %% Bins and bin center of growth rates
nbins = 50
xbincenter = Grow.loc[np.arange(nbins),'bins'].to_numpy()
start_bin = int(Grow.loc[50,'bins'])
end_bin = int(Grow.loc[51,'bins'])
perc_values = [5, 25, 50, 75, 95]
growfac = 2

# %% measurements
w1 = -1
w2 = 0
w3 = 0.05
w4 = 0.02
w5 = 0.01
w6 = 0.01
w7 = 0.01
w8 = 0.01
w9 = 0.01
w10 = 0.08
w11 = -0.02
w12 = 0.005


x1 = 0.17
x2s = 0.03
w1 = w6+x2s
x2 = x1+w2+x1
x3s = 0.03
x3 = (1-(w1+x1+w2+x1+w3+x3s+w4+x3s+w4+x3s+w5))/3
x4 = 0.2
x5 = 0.03
x6 = 0.2
x7 = 0.1
x8s = 0.075
x8 = 1-w6-x4-w7-x5-w8-x6-w9-x7-w12-x7-w10-x8s-w5
xa =x2
x9 = 0.2

h1 = 0.04
h2 = 0.02
h3 = 0.04
h4 = 0.06
h5 = 0.005
h6 = 0.05
h7 = 0.02
h8 = 0.02

y1 =  0.2
ya = 0.03
y2s = 0.03
y2 = 0.2
y3s = 0.03
y3 = ((h1+y1+ya+y2s+y2)-(y3s+h2+y3s))/2
y4 = 0.33
y5 = 1-(h1+y1+ya+y2s+y2+h3+y4+h5)
y6s = 0.085
y6 = 1-(h1+y1+ya+y2s+y2+h4+h5+y6s)
yh = h1+y1+ya+y2s+y2
y7 = (y5+h5-h6-h7-h8)/2

# %% other parameters
rot = -20
alpha = 0.5
lw_scatter=5

lw = 1
mstrlength = 10
fs = 12
fs_num = 13
fs_scatter = 12
fs_ann = 11
fn = 'Arial'

# %%
# Relative
from stemcellorganellesizescaling.analyses.utils.scatter_plotting_func import ascatter, oscatter, ocscatter
from stemcellorganellesizescaling.analyses.utils.grow_plotting_func import growplot

importlib.reload(
    sys.modules["stemcellorganellesizescaling.analyses.utils.scatter_plotting_func"]
)
importlib.reload(
    sys.modules["stemcellorganellesizescaling.analyses.utils.grow_plotting_func"]
)

from stemcellorganellesizescaling.analyses.utils.scatter_plotting_func import ascatter, oscatter, ocscatter
from stemcellorganellesizescaling.analyses.utils.grow_plotting_func import growplot


# %%layout
fig = plt.figure(figsize=(12, 12))
plt.rcParams.update({"font.size": fs})

# GrowCell
axGrowCell = fig.add_axes([w1, h1, x1, y1])
growplot(
    axGrowCell,
    'Cell volume_mean',
    ['TOMM20','LAMP1'],
    Grow,
    start_bin,
    end_bin,
    perc_values,
    growfac,
    structures,
    'left',
    fs_num,
)

# GrowNuc
axGrowNuc = fig.add_axes([w1+x1+w2, h1, x1, y1])
growplot(
    axGrowNuc,
    'Cell volume_mean',
    ['RAB5A','FBL'],
    Grow,
    start_bin,
    end_bin,
    perc_values,
    growfac,
    structures,
    'right',
    fs_num,
)

# Grow
axGrow = fig.add_axes([w6+x2s, h1+y1+ya+y2s, x2, y2])
# Grow bottom
axGrowB = fig.add_axes([w6+x2s, h1+y1+ya, x2, y2s])
# Grow side
axGrowS = fig.add_axes([w6, h1+y1+ya+y2s, x2s, y2])
# Plot
ps = data_root / statsIN / "cell_nuc_metrics"
ascatter(
    axGrow,
    axGrowB,
    axGrowS,
    HM['cellnuc_heatmap'][0],
    HM['cellnuc_heatmap'][2],
    HM['cellnuc_heatmap_abbs'][0],
    HM['cellnuc_heatmap_abbs'][2],
    cells,
    ps,
    kde_flag=True,
    fourcolors_flag=False,
    colorpoints_flag=True,
    rollingavg_flag=True,
    ols_flag=True,
    N2=1000,
    fs2=fs,
    fs=fs,
    typ=['vol','vol']
)
# Cell Size
xlim = axGrowB.get_xlim()
ylim = axGrowB.get_ylim()
tf = (0.108333**3)*1000
axGrowB.plot(tf*xbincenter[[start_bin, start_bin]], ylim, '--', linewidth=lw,color='red')
axGrowB.plot(tf*xbincenter[[end_bin, end_bin]], ylim, '--', linewidth=lw,color='red')

# Transition
axTransition = fig.add_axes([w1, h1+y1, xa, ya])
axTransition.set_xlim(left=xlim[0], right=xlim[1])
ylm = -1
axTransition.set_ylim(bottom=ylm, top=0)
axTransition.plot([xlim[0], tf*xbincenter[start_bin]], [ylm, 0], '--', linewidth=lw,color='darkred')
axTransition.plot([np.mean(xlim), tf*xbincenter[end_bin]], [ylm, 0], '--', linewidth=lw,color='darkred')
axTransition.plot([np.mean(xlim), tf*xbincenter[start_bin]], [ylm, 0], '--', linewidth=lw,color='orangered')
axTransition.plot([xlim[1], tf*xbincenter[end_bin]], [ylm, 0], '--', linewidth=lw, color='orangered')
axTransition.axis('off')

# Scale4
axScale4 = fig.add_axes([w1+x1+w2+x1+w3+x3s, y3s, x3, y3])
# Scale4 side
axScale4S = fig.add_axes([w1+x1+w2+x1+w3, y3s, x3s, y3])
# Scale4 bottom
axScale4B = fig.add_axes([w1+x1+w2+x1+w3+x3s, 0, x3, y3s])
# Plot compensated one
ps = data_root / statsIN / "cellnuc_struct_metrics"
oscatter(
    axScale4,
    axScale4B,
    axScale4S,
    HM['cellnuc_heatmap'][0],
    'FBL',
    HM['cellnuc_heatmap_abbs'][0],
    'FBL vol',
    'Structure volume',
    cells,
    ps,
    kde_flag=True,
    fourcolors_flag=False,
    colorpoints_flag=True,
    rollingavg_flag=True,
    ols_flag=True,
    N2=1000,
    fs2=fs,
    fs=fs,
    typ=['vol','vol'],
)

# Scale5
axScale5 = fig.add_axes([w1+x1+w2+x1+w3+x3s+x3+x3s+w4, y3s, x3, y3])
# Scale5 side
axScale5S = fig.add_axes([w1+x1+w2+x1+w3+x3+x3s+w4, y3s, x3s, y3])
# Scale5 bottom
axScale5B = fig.add_axes([w1+x1+w2+x1+w3+x3s+x3+x3s+w4, 0, x3, y3s])
# Plot
ps = data_root / statsIN / "cellnuc_struct_metrics"
oscatter(
    axScale5,
    axScale5B,
    axScale5S,
    HM['cellnuc_heatmap'][2],
    'FBL',
    HM['cellnuc_heatmap_abbs'][2],
    'FBL vol',
    'Structure volume',
    cells,
    ps,
    kde_flag=True,
    fourcolors_flag=False,
    colorpoints_flag=True,
    rollingavg_flag=True,
    ols_flag=True,
    N2=1000,
    fs2=fs,
    fs=fs,
    typ=['vol','vol'],
)

# Scale6
axScale6 = fig.add_axes([w1+x1+w2+x1+w3+x3s+x3+x3s+w4+x3+x3s+w4, y3s, x3, y3])
# Scale6 side
axScale6S = fig.add_axes([w1+x1+w2+x1+w3+x3+x3s+w4+x3+x3s+w4, y3s, x3s, y3])
# Scale6 bottom
axScale6B = fig.add_axes([w1+x1+w2+x1+w3+x3s+x3+x3s+w4+x3+x3s+w4, 0, x3, y3s])
ps = data_root / statsIN / "cellnuc_struct_COMP_metrics"
ocscatter(
    axScale6,
    axScale6B,
    axScale6S,
    HM["cellnuc_heatmap_COMP_metrics"][2],
    'FBL',
    HM["cellnuc_COMP_abbs"][2],
    'FBL *C',
    'Structure volume',
    HM["COMP_type"],
    HM["LIN_type"],
    cells_COMP,
    ps,
    kde_flag=True,
    fourcolors_flag=False,
    colorpoints_flag=True,
    rollingavg_flag=True,
    ols_flag=True,
    N2=1000,
    fs2=fs,
    fs=fs,
    typ=['vol','vol'],
)


# Scale1
axScale1 = fig.add_axes([w1+x1+w2+x1+w3+x3s, y3s+y3+h2+y3s, x3, y3])
# Scale1 side
axScale1S = fig.add_axes([w1+x1+w2+x1+w3, y3s+y3+h2+y3s, x3s, y3])
# Scale1 bottom
axScale1B = fig.add_axes([w1+x1+w2+x1+w3+x3s, 0+y3+h2+y3s, x3, y3s])
# Plot
ps = data_root / statsIN / "cellnuc_struct_metrics"
oscatter(
    axScale1,
    axScale1B,
    axScale1S,
    HM['cellnuc_heatmap'][0],
    'RAB5A',
    HM['cellnuc_heatmap_abbs'][0],
    'RAB5A vol',
    'Structure volume',
    cells,
    ps,
    kde_flag=True,
    fourcolors_flag=False,
    colorpoints_flag=True,
    rollingavg_flag=True,
    ols_flag=True,
    N2=1000,
    fs2=fs,
    fs=fs,
    typ=['vol','vol'],
)

# Scale2
axScale2 = fig.add_axes([w1+x1+w2+x1+w3+x3s+x3+x3s+w4, y3s+y3+h2+y3s, x3, y3])
# Scale2 side
axScale2S = fig.add_axes([w1+x1+w2+x1+w3+x3+x3s+w4, y3s+y3+h2+y3s, x3s, y3])
# Scale2 bottom
axScale2B = fig.add_axes([w1+x1+w2+x1+w3+x3s+x3+x3s+w4, 0+y3+h2+y3s, x3, y3s])
# Plot
ps = data_root / statsIN / "cellnuc_struct_metrics"
oscatter(
    axScale2,
    axScale2B,
    axScale2S,
    HM['cellnuc_heatmap'][0],
    'LAMP1',
    HM['cellnuc_heatmap_abbs'][0],
    'LAMP1 vol',
    'Structure volume',
    cells,
    ps,
    kde_flag=True,
    fourcolors_flag=False,
    colorpoints_flag=True,
    rollingavg_flag=True,
    ols_flag=True,
    N2=1000,
    fs2=fs,
    fs=fs,
    typ=['vol','vol'],
)

# Scale3
axScale3 = fig.add_axes([w1+x1+w2+x1+w3+x3s+x3+x3s+w4+x3+x3s+w4, y3s+y3+h2+y3s, x3, y3])
# Scale3 side
axScale3S = fig.add_axes([w1+x1+w2+x1+w3+x3+x3s+w4+x3+x3s+w4, y3s+y3+h2+y3s, x3s, y3])
# Scale3 bottom
axScale3B = fig.add_axes([w1+x1+w2+x1+w3+x3s+x3+x3s+w4+x3+x3s+w4, 0+y3+h2+y3s, x3, y3s])
# Plot
ps = data_root / statsIN / "cellnuc_struct_metrics"
oscatter(
    axScale3,
    axScale3B,
    axScale3S,
    HM['cellnuc_heatmap'][0],
    'TOMM20',
    HM['cellnuc_heatmap_abbs'][0],
    'TOMM20 vol',
    'Structure volume',
    cells,
    ps,
    kde_flag=True,
    fourcolors_flag=False,
    colorpoints_flag=True,
    rollingavg_flag=True,
    ols_flag=True,
    N2=1000,
    fs2=fs,
    fs=fs,
    typ=['vol','vol'],
)

# Annotation
axAnn = fig.add_axes([w6, yh+h3, x4, y4])
# Annotation
axAnn.imshow(num_st, aspect='auto', cmap='Pastel1')
for i in range(len(num_st)):
    for j in range(len(num_st.columns)):
        string = ann_st[i, j]
        if len(string) > mstrlength:
            string = string[0:mstrlength]
        text = axAnn.text(j, i, string,
                          ha="center", va="center", color=color_st.loc[i,'Color'], fontsize=fs_ann, fontname = fn)
axAnn.axis('off')

# Organelle Growth rates
axOrgGrow = fig.add_axes([w6+x4+w7, yh+h3, x5, y4])
axOrgGrow.imshow(np.expand_dims(growvec[:,0],axis=0).T, aspect='auto', cmap='viridis',vmin=0, vmax=100)
for i in range(len(growvec[:,0])):
        val = np.int(growvec[i, 0])
        text = axOrgGrow.text(0, i, val,
                          ha="center", va="center", color="w", fontsize=fs_num, fontweight='bold', fontname = fn)
axOrgGrow.set_yticks([])
axOrgGrow.set_yticklabels([])
axOrgGrow.set_xticks([])
axOrgGrow.text(0,1.03*len(growvec)-.5,'Scaling',horizontalalignment='center',verticalalignment = 'center', fontname = fn)
axOrgGrow.text(0,1.06*len(growvec)-.5,'rate (%)',horizontalalignment='center',verticalalignment = 'center', fontname = fn)

# Cell Growth rates
axCellGrow = fig.add_axes([w6+x4+w7, yh+h3+y4, x5, y5])
axCellGrow.imshow(growvecC, aspect='auto', cmap='viridis',vmin=0, vmax=120)
for i in range(len(growvecC)):
        val = np.int(growvecC[i, 0])
        text = axCellGrow.text(0, i, val,
                          ha="center", va="center", color="w", fontsize=fs_num, fontweight='bold', fontname = fn)
axCellGrow.set_yticks(range(len(HM["cellnuc_heatmap"])))
axCellGrow.set_yticklabels(HM["cellnuc_heatmap"],fontname = fn)
axCellGrow.set_xticks([])
axCellGrow.set_xticklabels([])

# Organelle Variance rates
axOrgVar = fig.add_axes([w6+x4+w7+x5+w8, yh+h3, x6, y4])
axOrgVar.imshow(pan, aspect='auto', cmap='seismic',vmin=-100, vmax=100)
for i in range(len(plot_array)):
    for j in range(len(plot_array.columns)):
        val = np.int(pan[i, j])
        text = axOrgVar.text(j, i, val,
                          ha="center", va="center", color="w", fontsize=fs_num, fontweight='bold',fontname = fn)
axOrgVar.set_yticks([])
axOrgVar.set_yticklabels([])
xlabels = HM["cellnuc_heatmap_abbs"]
axOrgVar.set_xticks([])
for j, xlabel in enumerate(xlabels):
    xls = xlabel.split( )
    axOrgVar.text(j,1.03*len(plot_array)-.5,xls[0],horizontalalignment='center',verticalalignment = 'center', fontname = fn)
    axOrgVar.text(j,1.06*len(plot_array)-.5,xls[1],horizontalalignment='center',verticalalignment = 'center', fontname = fn)

# Cell Variance rates
axCellVar = fig.add_axes([w6+x4+w7+x5+w8, yh+h3+y4, x6, y5])
axCellVar.imshow(panCN, aspect='auto', cmap='seismic',vmin=-100, vmax=100)
for i in range(len(plot_arrayCN)):
    for j in range(len(plot_arrayCN.columns)):
        val = np.int(panCN[i, j])
        text = axCellVar.text(j, i, val,
                          ha="center", va="center", color="w", fontsize=fs_num, fontweight='bold', fontname = fn)
axCellVar.set_yticks([])
axCellVar.set_yticklabels([])
axCellVar.set_xticks([])
axCellVar.set_xticklabels([])
axCellVar.axis('off')

# Cell Comp rates
axCompVarC= fig.add_axes([w6+x4+w7+x5+w8+x6+w9, yh+h3, x7, y4])
axCompVarC.imshow(panCompC, aspect='auto', cmap='seismic',vmin=-100, vmax=100)
for i in range(len(plot_arrayCompC)):
    for j in range(len(plot_arrayCompC.columns)):
        val = np.int(panCompC[i, j])
        text = axCompVarC.text(j, i, val,
                          ha="center", va="center", color="w", fontsize=fs_num, fontweight='bold', fontname = fn)
axCompVarC.set_yticks([])
axCompVarC.set_yticklabels([])
xlabels = HM["cellnuc_COMP_abbs"][0:2]
axCompVarC.set_xticks([])
for j, xlabel in enumerate(xlabels):
    xls = xlabel.split( )
    axCompVarC.text(j,1.03*len(plot_arrayCompC)-.5,xls[0],horizontalalignment='center',verticalalignment = 'center', fontname = fn)
    axCompVarC.text(j,1.06*len(plot_arrayCompC)-.5,xls[1],horizontalalignment='center',verticalalignment = 'center', fontname = fn)
# axCompVarC.set_title('Residual variance',verticalalignment='top')

# Nuc Comp rates
axCompVarN= fig.add_axes([w6+x4+w7+x5+w8+x6+w9+x7+w12, yh+h3, x7, y4])
axCompVarN.imshow(panCompN, aspect='auto', cmap='seismic',vmin=-100, vmax=100)
for i in range(len(plot_arrayCompN)):
    for j in range(len(plot_arrayCompN.columns)):
        val = np.int(panCompN[i, j])
        text = axCompVarN.text(j, i, val,
                          ha="center", va="center", color="w", fontsize=fs_num, fontweight='bold', fontname = fn)
axCompVarN.set_yticks([])
axCompVarN.set_yticklabels([])
xlabels = HM["cellnuc_COMP_abbs"][2:4]
axCompVarN.set_xticks([])
for j, xlabel in enumerate(xlabels):
    xls = xlabel.split( )
    axCompVarN.text(j,1.03*len(plot_arrayCompN)-.5,xls[0],horizontalalignment='center',verticalalignment = 'center', fontname = fn)
    axCompVarN.text(j,1.06*len(plot_arrayCompN)-.5,xls[1],horizontalalignment='center',verticalalignment = 'center', fontname = fn)
# axCompVarN.set_title('Residual variance',verticalalignment='top')

axExpVarBar= fig.add_axes([w6+x4+w7+x5+w8+x6+w11, yh+h3+y4+h6, x9, y7])
axExpVarBar.imshow(np.expand_dims(np.linspace(-100,100,201),axis=0), aspect='auto', cmap='seismic',vmin=-100, vmax=100)
text = axExpVarBar.text(0, 0, '-100', ha="left", va="center", color="w", fontsize=fs, fontweight='bold')
text = axExpVarBar.text(200, 0, '100', ha="right", va="center", color="w", fontsize=fs, fontweight='bold')
text = axExpVarBar.text(100, 0, '0', ha="center", va="center", color="k", fontsize=fs, fontweight='bold')
axExpVarBar.set_yticks([])
axExpVarBar.set_yticklabels([])
axExpVarBar.set_xticks([50, 150])
axExpVarBar.set_xticklabels(['Neg. corr.', 'Pos. corr.'],verticalalignment='center')
axExpVarBar.set_title('Explained Variance (%)',verticalalignment='top',fontsize=fs)

axGrowBar= fig.add_axes([w6+x4+w7+x5+w8+x6+w11, yh+h3+y4+h6+y7+h7, x9, y7])
axGrowBar.imshow(np.expand_dims(np.linspace(0,120,101),axis=0), aspect='auto', cmap='viridis',vmin=0, vmax=120)
text = axGrowBar.text(0, 0, '0', ha="left", va="center", color="w", fontsize=fs, fontweight='bold')
text = axGrowBar.text(50, 0, '60', ha="center", va="center", color="w", fontsize=fs, fontweight='bold')
text = axGrowBar.text(100, 0, '120', ha="right", va="center", color="w", fontsize=fs, fontweight='bold')
axGrowBar.set_yticks([])
axGrowBar.set_yticklabels([])
axGrowBar.set_xticks([])
axGrowBar.set_xticklabels([])
axGrowBar.set_title('Scaling rate relative to cell volume (%)',verticalalignment='top',fontsize=fs)

# # GrowVarS side
axGrowVarSS= fig.add_axes([w6+x4+w7+x5+w8+x6+w9+x7+w12+x7+w10+x8, yh+h4, x8s, y6])
yrange = [30, 85]
pos =  np.argwhere(np.logical_and(growvec[:,0]>yrange[0],growvec[:,0]<yrange[1]))
yarray = growvec[pos,0].squeeze()
temp = yarray.argsort()
ranks = np.empty_like(temp)
ranks[temp] = np.linspace(yrange[0],yrange[1],len(yarray))
growy = growvec[:,0].copy()
growy[pos] = np.expand_dims(ranks,axis=1)
for i in np.arange(len(growvec)):
    growval = growvec[i,0]
    struct = ann_st[i, 2]
    growyval = growy[i]
    axGrowVarSS.plot(0,growval,'.',markersize=10,color=color_st.loc[i,'Color'])
    axGrowVarSS.plot([0, 10], [growval, growyval], color=color_st.loc[i, 'Color'])
    axGrowVarSS.text(10,growyval, struct, fontsize=fs_scatter, color=color_st.loc[i, 'Color'], verticalalignment='center',fontweight='normal',horizontalalignment='left')
axGrowVarSS.set_ylim(bottom=0,top=125)
axGrowVarSS.set_xlim(left=0, right=75)
axGrowVarSS.axis("off")


# GrowVarS
axGrowVarS= fig.add_axes([w6+x4+w7+x5+w8+x6+w9+x7+w12+x7+w10, yh+h4, x8, y6])
for i in np.arange(len(growvec)):
    growval = growvec[i,0]
    growmin = growvec[i, 1]
    growmax = growvec[i, 2]
    struct = ann_st[i, 2]
    # if (struct == 'SON') or (struct == 'ATP2A2'):
    #     va = 'top'
    # else:
    #     va = 'baseline'
    # if (struct == 'HIST1H2BJ'):
    #     ha = 'right'
    # else:
    #     ha = 'left'
    axGrowVarS.plot(pan[i,0],growval,'.',markersize=10,color=color_st.loc[i,'Color'])
    axGrowVarS.plot([pan_min[i, 0], pan_max[i, 0]], [growval, growval], color=color_st.loc[i, 'Color'], alpha=alpha,linewidth=lw_scatter)
    axGrowVarS.plot([pan[i, 0], pan[i, 0]], [growmin, growmax], color=color_st.loc[i, 'Color'], alpha=alpha,linewidth=lw_scatter)
    # axGrowVarS.text(pan[i, 0],growval, struct, fontsize=fs_scatter, color=color_st.loc[i, 'Color'], verticalalignment=va,fontweight='bold',horizontalalignment=ha)
axGrowVarS.set_ylim(bottom=0,top=125)
axGrowVarS.set_xlim(left=0, right=75)
axGrowVarS.set_xlabel('Structure vol explained by cell vol (%)')
axGrowVarS.set_ylabel('Structure vol scaling as cell volume doubles  (%)')
axGrowVarS.grid()

# GrowVarS bottom
axGrowVarSB= fig.add_axes([w6+x4+w7+x5+w8+x6+w9+x7+w12+x7+w10, yh+h4+y6, x8+x8s, y6s])
xrange = [0, 75*(0.9*(x8s+x8)/x8)]
pos =  np.argwhere(np.logical_and(pan[:,0]>xrange[0],pan[:,0]<xrange[1]))
xarray = pan[pos,0].squeeze()
temp = xarray.argsort()
ranks = np.empty_like(temp)
ranks[temp] = np.linspace(xrange[0],xrange[1],len(xarray))
panx = pan[:,0].copy()
panx[pos] = np.expand_dims(ranks,axis=1)
for i in np.arange(len(growvec)):
    growval = growvec[i,0]
    struct = ann_st[i, 2]
    panxval = panx[i]
    axGrowVarSB.plot(pan[i,0],0,'.',markersize=10,color=color_st.loc[i,'Color'])
    axGrowVarSB.plot([pan[i,0], panxval], [0, 1], color=color_st.loc[i, 'Color'])
    axGrowVarSB.text(panxval, 1, struct, fontsize=fs_scatter, color=color_st.loc[i, 'Color'], verticalalignment='bottom',fontweight='normal',horizontalalignment='left',rotation=90)
axGrowVarSB.set_ylim(bottom=0,top=5)
axGrowVarSB.set_xlim(left=0, right=75*(0.9*(x8s+x8)/x8))
axGrowVarSB.axis("off")



plot_save_path = pic_root / f"heatmap_v3_20201104_FBLvol.png"
plt.savefig(plot_save_path, format="png", dpi=1000)
plt.close()

# plt.show()



