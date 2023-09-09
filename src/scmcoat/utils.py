"""
    utils.py
    June 23 2023
    
    functions to prepare emissions and other helpers
"""
from functools import cache
from json import loads as json_loads
from importlib.resources import files

import pandas as pd
import numpy as np
import xarray as xr

from fair.constants import molwt
from fair.constants.general import ppm_gtc
from fair.constants.general import EARTH_RADIUS, SECONDS_PER_YEAR

from scmcoat import ClimateParams
from scmcoat.core import FAIR_EMISSIONS_GASES

# TODO: Use something more stable like a DOI link? 
@cache
def download_emissions_csv(url="https://rcmip-protocols-au.s3-ap-southeast-2.amazonaws.com/v5.1.0/rcmip-emissions-annual-means-v5-1-0.csv"):
    return pd.read_csv(url)

# This code credited to Chris Smith AR6 repo
# From https://github.com/chrisroadmap/ar6/blob/main/notebooks/190_WG3_run-constrained-fair-ensemble-concentration-driven.ipynb
#   from the SSP245 cell
def rcmip_emissions(scenario):
    
    units = ['Gt C/year',
             'Gt C/year',
             'Mt CH4/yr',
             'tonnes N2/year',
             'Mt S/year',
             'Mt CO/yr',
             'Mt VOC/yr',
             'Mt N/year',
             'Mt BC/yr',
             'Mt OC/yr',
             'Mt NH3/yr',
             'kt CF4/yr',
             'kt C2F6/yr',
             'kt C6F14/yr',
             'kt HFC23/yr',
             'kt HFC32/yr',
             'kt HFC4310mee/yr',
             'kt HFC125/yr',
             'kt HFC134a/yr',
             'kt HFC143a/yr',
             'kt HFC227ea/yr',
             'kt HFC245fa/yr',
             'kt SF6/yr',
             'kt CFC11/yr',
             'kt CFC12/yr',
             'kt CFC113/yr',
             'kt CFC114/yr',
             'kt CFC115/yr',
             'kt CCl4/yr',
             'kt CH3CCl3/yr',
             'kt HCFC22/yr',
             'kt HCFC141b/yr',
             'kt HCFC142b/yr',
             'kt Halon1211/yr',
             'kt Halon1202/yr',
             'kt Halon1301/yr',
             'kt Halon2402/yr',
             'kt CH3Br/yr',
             'kt CH3Cl/yr']
    
    NTOA_ZJ = 4 * np.pi * EARTH_RADIUS**2 * SECONDS_PER_YEAR * 1e-21 
    
    emis_all = download_emissions_csv()
    expt = scenario
    # emis_all = pd.read_csv('../data_input_large/rcmip-emissions-annual-means-v5-1-0.csv')
    emis_subset = emis_all[(emis_all['Scenario']==expt)&(emis_all['Region']=='World')]

    species=['CO2|MAGICC Fossil and Industrial','CO2|MAGICC AFOLU','CH4','N2O','Sulfur','CO','VOC','NOx','BC','|OC','NH3',
             'CF4','C2F6','C6F14','HFC23','HFC32','HFC4310mee','HFC125','HFC134a','HFC143a',
             'HFC227ea','HFC245fa','SF6','CFC11','CFC12','CFC113','CFC114','CFC115','CCl4','CH3CCl3','HCFC22',
             'HCFC141b','HCFC142b','Halon1211','Halon1202','Halon1301','Halon2402','CH3Br','|CH3Cl']
    # print(len(species))
    emis = np.zeros((751,40))
    emis[:,0] = np.arange(1750,2501)
    for ie, specie in enumerate(species):
        try:
            tmp = emis_subset[emis_subset.Variable.str.endswith(specie)].loc[:,'1750':'2500'].values.squeeze()
            emis[:,ie+1] = pd.Series(tmp).interpolate().values
        except:
            emis[:,ie+1] = 0
    if expt not in ("rcp26", "rcp45", "rcp60", "rcp85"): # is aviNOx ever used????
        tmp = emis_subset[emis_subset['Variable']=='Emissions|NOx|MAGICC Fossil and Industrial|Aircraft'].loc[:,'1750':'2500'].values.squeeze()    
        aviNOx = pd.Series(tmp).interpolate().values
        aviNOx_frac = aviNOx/emis[:,8]
    #
    unit_convert = np.ones(40)
    unit_convert[1]=0.001 * molwt.C/molwt.CO2
    unit_convert[2]=0.001 * molwt.C/molwt.CO2
    unit_convert[4]=0.001 * molwt.N2/molwt.N2O
    unit_convert[5]=molwt.S/molwt.SO2
    unit_convert[8]=molwt.N/molwt.NO2

    emis = emis * unit_convert

    # conc_all = pd.read_csv("~/ClimateImpactLab/Climate/FAIR/raw_data_large/rcmip-concentrations-annual-means-v5-1-0.csv")
    # conc_subset = conc_all[(conc_all['Scenario']==expt)&(conc_all['Region']=='World')]
    # gases=['CO2','CH4','N2O','CF4','C2F6','C6F14','HFC23','HFC32','HFC4310mee','HFC125','HFC134a','HFC143a',
    #        'HFC227ea','HFC245fa','SF6','CFC11','CFC12','CFC113','CFC114','CFC115','CCl4','CH3CCl3','HCFC22',
    #        'HCFC141b','HCFC142b','Halon1211','Halon1202','Halon1301','Halon2402','CH3Br','CH3Cl']
    # conc = np.zeros((751,31))
    # for ig, gas in enumerate(gases):
    #     try:
    #         tmp = conc_subset[conc_subset.Variable.str.endswith(gas)].loc[:,'1750':'2500'].values.squeeze()
    #         conc[:,ig] = pd.Series(tmp).interpolate().values
    #     except:
    #         conc[:,ig] = 0

    # emisds = emis.to_xarray().to_array().rename({"variable":"gas",
    #                                     "index":"year"})
    # emisds = emisds.assign_coords(year=emisds.isel(gas=0).values)
    emisds = xr.DataArray(emis, coords={"year":emis[:,0],
                               "gas":["year"]+FAIR_EMISSIONS_GASES})
    emisds["units"] = xr.DataArray(units, coords = {"gas": emisds.gas[1:]})
    return emisds #, conc


def _get_climateparamsdata(filename: str) -> bytes:
    return files(f"{__package__}.climateparams_data").joinpath(filename).read_bytes()


def _inflate_climateparamsdata(
    *, slim_fl: [str | bytes | None] = None, common_fl: [str | bytes | None] = None
) -> list[dict]:
    if slim_fl is None:
        slim_fl = _get_climateparamsdata("fair-1.6.2-wg3-params-slim.json")
    if common_fl is None:
        common_fl = _get_climateparamsdata("fair-1.6.2-wg3-params-common.json")

    slim = json_loads(slim_fl)
    common = json_loads(common_fl)
    return [d | common for d in slim]


def _climateparamslist2ds(config_list: list[dict]) -> xr.Dataset:
    pass


def get_fairv1_climateparams() -> ClimateParams:
    """
    Get ClimateParams instance from FaIR v1.6.2 WG3 calibrated and constrained parameter set

    This data is stored within the package and does not require internet
    access. The original data is available online at
    https://doi.org/10.5281/zenodo.6601980
    """
    return ClimateParams(params=_climateparamslist2ds(_inflate_climateparamsdata()))
