"""
All the functions
"""
import os
import sys
import pdb

import numpy as np
import pandas as pd

from functools import reduce
from scipy.integrate import quad

from physconst import *
from toybands.config import *


def lldirac_gen(B, B_perp, N, is_cond, gfactor, M, vf):
    """Calculate the energy of Landau level in Dirac dispersion with a Zeeman term
    Arguments:
    B: Total magnetic field (IU,Tesla)
    B_perp: The perpendicular component of B (IU,Tesla)
    N: Landau index
    is_cond: True for conduction and False for valence band
    gfactor: g-factor
    M: mass term
    vf: Fermi-velocity (m/s)
    Return:
    Energy (IU)
    """
    if N < 0 or not isinstance(N, int):
        raise ValueError(f"your input N = {N} should be an integer no less than zero")
    if gfactor < 0:
        raise ValueError(f"your input gfactor = {gfactor} <0")
    alpha = 1 if is_cond else -1
    return (
        alpha
        * (2 * e0 * hbar * vf ** 2 * B_perp * N + (gfactor * muB * B/2) ** 2 + (M*e0) ** 2)
        ** 0.5
    )
    ## Reference for the massive Dirac-like E-B relationship: Physical Review B 96,041101(R)(2017)

def llconv_gen(B, B_perp, N, is_cond, spin, gfactor, meff):
    """Calculate the energy of Landau level in conventional dispersion with a Zeeman term
    Arguments:
    B: Total magnetic field (IU,Tesla)
    B_perp: The perpendicular component of B (IU,Tesla)
    is_cond: Conduction band (True) or valence band (False)
    spin: spin indicator
    gfactor: g-factor 
    meff: effective mass in units of the rest mass of electron (me)
    Return:
    Energy (IU)
    """
    if not spin in [1.0, -1.0, 1, -1]:
        raise ValueError(f"your input spin ={spin} is neither 1 or -1")
    alpha = 1 if is_cond else -1
    return alpha*(N + 0.5) * hbar * e0 * B_perp / meff/ me + spin * gfactor * muB * B / 2

def den2en(density,is_dirac,is_cond,vf,meff):
        if is_dirac and is_cond:
            return -hbar * vf * (4 * np.pi * density) ** 0.5
        elif is_dirac and not is_cond:
            return hbar * vf * (4 * np.pi * density) ** 0.5
        elif not is_dirac and is_cond:
            return -(hbar ** 2) * density/ np.pi / meff/ me
        elif not is_dirac and not is_cond:
            return (hbar ** 2) * density / np.pi / meff/ me


def _e_integral(func, ymin, y_list, args):
    if not isinstance(y_list, list):
        raise ValueError("ylist is not a list")
    if not isinstance(args, tuple):
        raise ValueError("args must be a tuple")
    output = []
    prev_result = 0
    try:
        yint = abs(y_list[0] - y_list[1])
    except:
        yint = 0
    for index, y in enumerate(y_list):
        if y > ymin + yint and index == 0:
            result = quad(func, ymin, y, args=args)[0]
        elif y > ymin + yint and index > 0:
            result = quad(func, y - yint, y, args=args)[0]
        elif y <= ymin:
            result = 0
        else:
            result = quad(func, ymin, y, args=args)[0]
        result = result + prev_result
        prev_result = result
        output.append(result)
    return output


def _h_integral(func, ymax, y_list, args):
    if not isinstance(y_list, list):
        raise ValueError("ylist is not a list")
    if not isinstance(args, tuple):
        raise ValueError("args must be a tuple")
    output = []
    prev_result = 0
    try:
        yint = abs(y_list[0] - y_list[1])
    except:
        yint = 0
    for index, y in enumerate(sorted(y_list, reverse=True)):
        if y < ymax - yint and index == 0:
            result = quad(func, y, ymax, args=args)[0]
        elif y < ymax - yint and index > 0:
            result = quad(func, y, y + yint, args=args)[0]
        elif y >= ymax:
            result = 0
        else:
            result = quad(func, y, ymax, args=args)[0]
        result = result + prev_result
        prev_result = result
        output.append(result)
    output.reverse()
    return output


def e_density_of_state(E, B, sigma, angle_in_deg, e_lls, compensate_on=False):
    """Calculate the density of state at a set of certain chemical potential and magnetic field for top/bottom surface states
    Arguments:
    E: position of chemical potential
    B: total magnetic field
    sigma: broadening of Landau level by assuming a Gaussian-shape distribution around the central energy
    angle_in_deg: the angle of magnetic field with the normal of sample plane
    e_lls: energy of Landau levels from electron side
    compensate_on: if taking into account Dirac-like 1/2 filling factor
    Return:
    Density of state from all the bands at (E,B) 
    """
    # degeneracy of Landau levels at a certain field
    lldegeneracy = B * np.cos(angle_in_deg * np.pi / 180) * e0 / h0
    compensate = 0.5 * lldegeneracy * np.exp(-0.5 * (E - min(e_lls)) ** 2 / sigma ** 2) / sigma / (
            2 * np.pi) ** 0.5
    # both top and bottom surfaces right at the chemical potential
    output = reduce(
        (lambda x, y: x + y),
        [
            lldegeneracy
            * np.exp(-0.5 * (E - e_ll) ** 2 / sigma ** 2)
            / sigma
            / (2 * np.pi) ** 0.5
            for e_ll in e_lls
        ],
    )
    return output-compensate if compensate else output 


def h_density_of_state(E, B, sigma, angle_in_deg, h_lls, compensate_on=False):
    """Calculate the density of state at a set of certain chemical potential and magnetic field for top/bottom surface states
    Arguments:
    E: position of chemical potential
    B: total magnetic field
    sigma: broadening of Landau level by assuming a Gaussian-shape distribution around the central energy
    angle_in_deg: the angle of magnetic field with the normal of sample plane
    h_lls: energy of Landau levels from hole side
    compensate_on: if taking into account Dirac-like 1/2 filling factor
    Return:
    Density of state from all the bands at (E,B)
    """
    # degeneracy of Landau levels at a certain field
    lldegeneracy = B * np.cos(angle_in_deg * np.pi / 180) * e0 / h0
    compensate = 0.5 * lldegeneracy * np.exp(-0.5 * (E - min(h_lls)) ** 2 / sigma ** 2) / sigma / (
            2 * np.pi) ** 0.5
    # both top and bottom surfaces right at the chemical potential
    output = reduce(
        (lambda x, y: x + y),
        [
            -lldegeneracy
            * np.exp(-0.5 * (E - h_ll) ** 2 / sigma ** 2)
            / sigma
            / (2 * np.pi) ** 0.5
            for h_ll in h_lls
        ],
    )
    return output+compensate if compensate_on else output


def e_idos_gen(e_list, B, sigma, angle_in_deg, e_lls, compensate_on=False):
    lowest_ll_eng = min(e_lls)
    output = _e_integral(
        e_density_of_state,
        lowest_ll_eng - 3 * sigma,
        e_list,
        (B, sigma, angle_in_deg, e_lls,compensate_on),
    )
    return output


def h_idos_gen(e_list, B, sigma, angle_in_deg, h_lls, compensate_on=False):
    highest_ll_eng = max(h_lls)
    output = _h_integral(
        h_density_of_state,
        highest_ll_eng + 3 * sigma,
        e_list,
        (B, sigma, angle_in_deg, h_lls,compensate_on),
    )
    return output


def add_list(a, b):

    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        output = []
        for aa, bb in zip(a, b):
            output.append(aa + bb)
        return output
    elif not isinstance(a, list) or not isinstance(b, list):
        raise TypeError("Input must be a list")
    elif len(a) != len(b):
        raise ValueError("Two lists must be of the same length")


def extract_list(xlist,bool_list):
    if not len(xlist) == len(bool_list):
        sys.stderr.write('The list and bool_list must be of the same length')
    output = []
    for x,bool in zip(xlist,bool_list):
        if bool:
            output.append(x)
    return output


def pretty_print(df):
    if not isinstance(df,pd.DataFrame):
        sys.stderr.write('Input is not a pandas.DataFrame object')
    names = list(df.columns)
    if 'density' in names:
        l = [value/1e16 for value in df['density'].values.tolist()]
        df = df.assign(density=l).rename(columns={'density':'density(1e16/m2)'})

    if 'Ebb' in names:
        l = [value/e0 for value in df['Ebb'].values.tolist()]
        df = df.assign(Ebb=l).rename(columns={'Ebb':'Ebb(eV)'}) 

    if 'vf' in names:
        l = [value/1e6 for value in df['vf'].values.tolist()]
        df = df.assign(vf=l).rename(columns={'vf':'vf(1e6m/s)'})
    print(df)



def system_stamp_csv(args,jsfilename=None):
    csvfilename = args.fnm
    if jsfilename == None:
        jsfilename = os.path.join(os.getcwd(),'system.json')
    try:
        df = pd.read_json(jsfilename)
    except:
        sys.stderr.write('Failed to load JSON file for your system\n')
    try:
        if len(csvfilename.split('.'))==1:
            path = os.path.join(DEFAULT_PATH,csvfilename+'_sysinfo'+'.csv')
        else:
            path =os.path.join(DEFAULT_PATH,csvfilename.split('.')[-2]+'_sysinfo'+'.csv')
        df.to_csv(path,mode='w')
    except:
        sys.stderr.write('Failed to stamp your sysinfo into csv file\n')


def read_den_from_csv(csvfilename):
    if os.path.isfile(csvfilename) and csvfilename.endswith('.csv'):
        df = pd.read_csv(csvfilename,header=None)
    else:
        sys.stderr.write(f'The file {csvfilename} does not exist or not .csv file')
        exit()
    output = []
    for column in df.columns:
        output.append([10000*den for den in df[column].tolist()])
    output = np.array(output)
    output = np.transpose(output)
    return output

def extents(f):
    '''
    Calculate the extent parameter for mapping-like plots:
    extent=[horizontal_min,horizontal_max,vertical_min,vertical_max]
    :param f: list type x-vector or y-vector
    :return:
    '''
    delta = f[1] - f[0]
    return [f[0] - delta/2, f[-1] + delta/2]

def ElementTree_pretty(elem):
    from xml.etree import ElementTree
    from xml.dom import minidom
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")