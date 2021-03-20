import argparse
import os
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pdb
from tqdm import tqdm

from utils import flattenList, div
from toybands.functions import *
from toybands.classes import *
from toybands.plottools import (make_n_colors, make_1d_E_B_plots, make_1d_den_B_plots, super_save, make_slices,make_canvas)

def multi_floats(value):
    values = value.split()
    values = map(float, values)
    return list(values)


def run():
    my_parser = argparse.ArgumentParser(
        prog="run", description="A band model to play with"
    )

    my_parser.add_argument(
        "-enplot",
        action="store_true",
        help="plot the energy versus bfield (yes/no)",
    )

    my_parser.add_argument(
        "-denplot",
        action="store_true",
        help="plot the density versus bfield (yes/no)",
    )

    my_parser.add_argument(
        "-simu",
        action="store_true",
        help="dynamically generate relationship between the density and the bfield at steps of input density (yes/no)",
    )

    my_parser.add_argument(
        "--allden",
        action="store",
        type = multi_floats,
        help="densities for each band: start1 end1 start2 end2 .... ",
    )

    my_parser.add_argument(
        "-nos",
        action="store",
        type= int,
        help="number of steps in the simulation ",
    )

    my_parser.add_argument(
        "-dir",
        action="store",
        help="relative output directory",
    )

    my_parser.add_argument(
        "-fnm",
        action="store",
        help="filename",
    )

    my_parser.add_argument(
        "--enrange",
        action="store",
        type=float,
        nargs=3,
        help="energy range: start end numofpoints",
    )

    my_parser.add_argument(
        "--bfrange",
        action="store",
        type=float,
        nargs=3,
        help="magnetic field range: start end numofpoints",
    )

    my_parser.add_argument(
        "-nmax",
        action="store",
        type=int,
        default=20,
        help="number of Landau levels involved (default=20)",
    )

    my_parser.add_argument(
        "-angle",
        action="store",
        type=float,
        default=0,
        help="angle in degree made with the sample plane norm by the external field (default=0)",
    )

    args = my_parser.parse_args()
    print(vars(args))
    return args


def enplot(args,newsystem,bfrange,enrange):
    if args.nmax is not None and args.angle is not None:
        y_databdl = [
            [
                band.cal_energy(bfrange, args.nmax, args.angle)[
                    f"#{N}"
                ].tolist()
                for N in range(args.nmax)
            ]
            for band in newsystem.bands
        ]
        colors = make_n_colors(len(y_databdl), "jet", 0.1, 0.9)
        mu_pos = [
            newsystem.mu(
                np.linspace(
                    min(flattenList(y_databdl)),
                    max(flattenList(y_databdl)),
                    100,
                ).tolist(),
                B,
                args.nmax,
                args.angle,
                sigma=abs(enrange[1] - enrange[0]),
            )
            for B in bfrange
        ]
        make_1d_E_B_plots(bfrange, y_databdl, colors, mu_pos)
        newsystem.databdl_write_csv(args.fnm,bfrange,y_databdl,'enplot')
        super_save(args.fnm, args.dir)
    else:
        sys.stderr.write("The arguments -nmax and -angle are needed")

def denplot(args,newsystem,bfrange,enrange):
    if args.nmax is not None and args.angle is not None:
        IDOS = [
            newsystem.dos_gen(
                enrange, B, args.nmax, args.angle, abs(enrange[1] - enrange[0])
            )
            for B in bfrange
        ]
        # bundle data from each Landau level originating from each band
        y_databdl = [
            [
                [
                    np.interp(x=x, xp=enrange, fp=IDOS[index])
                    for index, x in enumerate(
                        band.cal_energy(bfrange, args.nmax, args.angle)[
                            f"#{N}"
                        ].tolist()
                    )
                ]
                for N in range(args.nmax)
            ]
            for band in newsystem.bands
        ]
        colors = make_n_colors(len(y_databdl), "jet", 0.1, 0.9)
        tot_den = newsystem.tot_density()
        make_1d_den_B_plots(bfrange, y_databdl, colors, tot_den)
        newsystem.databdl_write_csv(args.fnm,bfrange,y_databdl,'denplot')
        super_save(args.fnm, args.dir)
    else:
        sys.stderr.write('The arguments -nmax and -angle are needed')

def simu(args,newsystem,bfrange,enrange):
    if args.nmax is not None and args.angle is not None and args.allden is not None and args.nos is not None:
        den_slices = make_slices(args.allden,args.nos)
        tot_den_list = [sum(den_slice) for den_slice in den_slices]
        tot_den_int = abs(tot_den_list[0]-tot_den_list[1])
        ax = make_canvas()
        for den_slice in tqdm(den_slices):
            newsystem.set_all_density(den_slice)
            IDOS = [newsystem.dos_gen(enrange, B, args.nmax, args.angle, abs(enrange[1]-enrange[0])) for B in bfrange]
            y_databdl = [[[np.interp(x=x, xp=enrange, fp=IDOS[index]) for index, x in enumerate(band.cal_energy(bfrange,args.nmax,args.angle)[f'#{N}'].tolist())] for N in range(args.nmax)] for band in newsystem.bands]
            colors = make_n_colors(len(y_databdl),'jet',0.1,0.9)
            tot_den = newsystem.tot_density()
            plotrange = [tot_den-0.5*tot_den_int,tot_den+0.5*tot_den_int]
            make_1d_den_B_plots(bfrange,y_databdl,colors,tot_den,ax=ax,plotrange=plotrange)
            newsystem.databdl_write_csv(args.fnm,bfrange,y_databdl,'simu',plotrange=plotrange)
        super_save(args.fnm,args.dir)
    else:
        sys.stderr.write('The arguments -nmax and -angle and -allden and -nos are needed')

if __name__ == "__main__":
    args = run()
    if os.path.isfile("system.json"):
        df = pd.read_json("system.json")
        newsystem = System()
        for i in range(len(df)):
            dt = df.iloc[i].to_dict()
            newband = Band(
                density=dt["density"],
                is_cond=dt["is_cond"],
                is_dirac=dt["is_dirac"],
                gfactor=dt["gfactor"],
                meff=dt["meff"],
                spin=dt["spin"],
                M=dt["M"],
                vf=dt["vf"],
            )
            newsystem.add_band(newband)
        enrange = list(
            np.linspace(
                args.enrange[0] * e0, args.enrange[1] * e0, int(args.enrange[2])
            )
        )
        bfrange = list(
            np.linspace(args.bfrange[0], args.bfrange[1], int(args.bfrange[2]))
        )
        if args.enplot:
            enplot(args,newsystem,bfrange,enrange)
        if args.denplot:
            denplot(args,newsystem,bfrange,enrange)
        if args.simu:
            simu(args,newsystem,bfrange,enrange)
    else:
        sys.stderr.write("no system (system.json) exist")