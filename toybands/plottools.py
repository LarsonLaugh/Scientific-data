import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as mplcm
import matplotlib.colors as mplcolors
import pdb
from physconst import *
from utils import flattenList, div
from toybands.functions import extract_list

# define the norm in plotting
plt.rc('lines', lw=1, color='k')  # thicker black lines
plt.rc('grid', c='0.5', ls='-', lw=0.5)  # solid gray grid lines
plt.rc('savefig', dpi=600)  # higher res outputs
plt.rc("font", size=20, family='arial', weight='light')
plt.rc("axes", labelsize=20, titlesize=20, linewidth=1)
plt.rc("xtick", direction='in', labelsize=20)
plt.rc('xtick.major', size=10, pad=7)
plt.rc('xtick.minor', size=5, pad=7, visible=True)
plt.rc("ytick", direction='in', labelsize=20)
plt.rc('ytick.major', size=10, pad=7)
plt.rc('ytick.minor', size=5, pad=7, visible=True)
plt.rc("legend", fontsize=20)
plt.rcParams['figure.constrained_layout.use'] = True

DEFAULT_PATH = os.path.join(os.getcwd(),'output')
ALLOW_FORMAT = ['pdf','png','jpeg','tiff']
DEFAULT_FORMAT = 'pdf'

def make_n_colors(n,cmap,vstart,vend):
    if not isinstance(n,int):
        raise TypeError('n must be an integer')
    if not isinstance(cmap,str):
        raise TypeError('cmap should be the name of an existing cmap instance')
    if vstart>1 or vstart<0:
        raise ValueError('vstart should be in [0.0,1.0]')
    if vend>1 or vend<0:
        raise ValueError('vend should be in [0.0,1.0]')
    try:
        cmap = mplcm.get_cmap(cmap)
    except:
        raise ValueError('failed to fetch colormap {cmap}')
    colors_list = np.linspace(vstart,vend,n).tolist()
    colors = [cmap(x) for x in colors_list]
    return colors

def make_1d_E_B_plots(bfrange,y_databdl,colors, mu_pos = None,enrange=None,figsize=(10,10),linewidth=2):
    if not isinstance(bfrange,list) or not isinstance(y_databdl,list) or not isinstance(colors,list):
        raise TypeError(f'either x_databdl or y_databdl or colors is not list')
    if not len(y_databdl)==len(colors):
        raise ValueError(f'y_databdl, colors are not of the same length')
    if not any(isinstance(el, list) for el in y_databdl):
        raise TypeError(f'y_databdl is not nested list')
    if not isinstance(figsize,tuple):
        raise TypeError(f'figsize should be a tuple like (10,10)')
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)
    for y_data, color in zip(y_databdl,colors):
        for y in y_data:
            ax.plot(bfrange,div(y,e0),linewidth=linewidth,color=color)
    if mu_pos and len(mu_pos)==len(bfrange):
        ax.plot(bfrange,div(mu_pos,e0),linewidth=linewidth,color='k')
    if enrange is not None:
        ax.set_ylim(min(enrange)/e0,max(enrange)/e0)
    ax.set_xlabel('$B$ [T]')
    ax.set_ylabel('$E$ [eV]')

def make_1d_den_B_plots(bfrange,y_databdl,colors, tot_den = None,enrange=None,figsize=(10,10),linewidth=2,ax=None,plotrange = None):
    if not isinstance(bfrange,list) or not isinstance(y_databdl,list) or not isinstance(colors,list):
        raise TypeError(f'either x_databdl or y_databdl or colors is not list')
    if not len(y_databdl)==len(colors):
        raise ValueError(f'y_databdl, colors are not of the same length')
    if not any(isinstance(el, list) for el in y_databdl):
        raise TypeError(f'y_databdl is not nested list')
    if not isinstance(figsize,tuple):
        raise TypeError(f'figsize should be a tuple like (10,10)')
    if ax is None:
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
    if plotrange is None:
        for y_data, color in zip(y_databdl,colors):
            for y in y_data:
                ax.plot(bfrange,y,linewidth=linewidth,color=color)
    else:
        for y_data, color in zip(y_databdl,colors):
            for y in y_data:
                ax.scatter(extract_list(bfrange,[yy>plotrange[0] and yy<plotrange[1] for yy in y]),extract_list(y,[yy>plotrange[0] and yy<plotrange[1] for yy in y]), color=color)
    if tot_den is not None:
        ax.axhline(y = tot_den, linewidth=linewidth, color='k')
    if enrange is not None:
        ax.set_ylim(min(enrange)/e0,max(enrange)/e0)

    ax.set_xlabel('$B$ [T]')
    ax.set_ylabel('$n$ [1/m$^2$]')

def make_canvas(figsize=(10,10)):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)
    return ax

def super_save(filename=None,path=None):
    if filename is None:
        filename = '[auto]default'
    if path is None:
        path = DEFAULT_PATH
    if not os.path.isdir(path):
        os.mkdir(path)
        sys.stdout.write(f'path created under {path}')
    if len(filename.split('.'))>1:
        fmt = filename.split('.')[-1]
        if fmt in ALLOW_FORMAT:
            plt.savefig(os.path.join(path,filename))
        else:
            sys.stderr.write(f'The format {fmt} is not supported')
    else:
        plt.savefig(os.path.join(path, filename+'.'+DEFAULT_FORMAT))
        sys.stdout.write(f'By default, saved as a {DEFAULT_FORMAT} file')


def make_slices(den_list,numofsteps):
    if not isinstance(den_list, list):
        sys.stderr.write('Input is not list')
    all_density  = []
    for start,end in zip(den_list[::2],den_list[1::2]):
        all_density.append(np.linspace(start,end,numofsteps).tolist())
    all_density = np.array(all_density)
    output = np.transpose(all_density)
    return output