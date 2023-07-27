"""
    core.py
    June 23 2023
    
    functions to run FaIR simple climate model given emissions
"""

import numpy as np
import xarray as xr
import fair
from dataclasses import dataclass

FAIR_EMISSIONS_GASES = ['CO2_Fossil',
                'CO2_Land',
                'CH4',
                'N2O',
                'SOx',
                'CO',
                'NMVOC',
                'NOx', 
                'BC', 
                'OC',
                'NH3',
                'CF4',
                'C2F6',
                'C6F14',
                'HFC23',
                'HFC32',
                'HFC4310mee',
                'HFC125',
                'HFC134a',
                'HFC143a',
                'HFC227ea',
                'HFC245fa',
                'SF6',
                'CFC11',
                'CFC12',
                'CFC113',
                'CFC114',
                'CFC115',
                'CARB_TET',
                'MCF',
                'HCFC22',
                'HCFC141b',
                'HCFC142b', 
                'Halon1211',
                'Halon1202',
                'Halon1301',
                'Halon2402',
                'CH3Br', 
                'CH3Cl' ]


#TODO: require specific climate param settings for FaIR?
#  This current set up has a lot of specificity in that
#  running FaIR expects very specific data variables in the 
#  ClimateParams.params Dataset (so far this is not enforced).
@dataclass
class ClimateParams:
    """
        Currently, the setup of FairModel expects that ClimateParams.params
        is from the xr.Dataset of the AR6 JSON
        file containing FaIR climate parameters used in the report. The
        arguments with time dimensions are all of length 751 (reference year
        1750).
        TODO point to the param processing and creation of netcdf file.
    """
    params: xr.Dataset

    @property
    def median_params(self):
        
        # drop string arguments
        pdropped = self.params.drop(["ghg_forcing","tropO3_forcing"])
        # take the median of numerical args
        pmedian = pdropped.median(dim="simulation")
        # add string args back to dataset
        pmedian["ghg_forcing"] = self.params["ghg_forcing"]
        pmedian["tropO3_forcing"] = self.params["tropO3_forcing"]
        
        return pmedian

class FairModel:
    """
        implementation of the ClimateModel Protocol
    """
    
    def __init__(self, params=None, debug=False):
        self.params = params
        self.simid = "default"
        self.debug = debug
    def __repr__(self):
        return f"{type(self).__name__}(params={self.params!r}, simid={self.simid})"
    
    def get_list_of_concentration_gases(self):
        """
            returns a list of gas names in the order of the `concentration` response
            to a run of FairModel
            
            TODO remove getter. Access the attribute directly
        """
        conc_gas_species_names = [
            "co2",
            "ch4",
            "n2o",
            "cf4",
            "c2f6",
            "c6f14",
            "hfc23",
            "hfc32",
            "hfc43_10",
            "hfc125",
            "hfc134a",
            "hfc143a",
            "hfc227ea",
            "hfc245fa",
            "sf6",
            "cfc11",
            "cfc12",
            "cfc113",
            "cfc114",
            "cfc115",
            "carb_tet",
            "mcf",
            "hcfc22",
            "hcfc141b",
            "hcfc142b",
            "halon1211",
            "halon1202",
            "halon1301",
            "halon2402",
            "ch3br",
            "ch3cl",
        ]
        return conc_gas_species_names


    def _run(self, emiss, useMultigas=True):

        # === move next block to utils?
        if self.params is None:

            if self.debug:
                print(f"Running default FaIR, v{fair.__version__}")
            # ignore simid
            ret = fair.forward.fair_scm(emissions=emiss, useMultigas=useMultigas)
            return ret
        else:
            if self.simid == "default":
                if self.debug:
                    print("ClimateParams are not None and simid='default'. Running with median_params.")
                    
                self.simid = "median"
                
            if self.simid == "median":
                args = self.params.median_params
            else:
                args = self.params.params.sel(simulation=self.simid)
            if self.debug:
                print(f"Running FaIR, v{fair.__version__}. simid: {self.simid}")
        # ===
        
            if not useMultigas:
                raise NotImplementedError("can't run in CO2-only mode with args @@@@for now")

            # default time dimensions for different versions of FaIR v1.*
            # TODO generalize time dim. 
            # TODO test different length of emissions time series
            if emiss.shape[0] == 736:
                reference_year = 1765

                nt = 736 
                F_solar = np.zeros(nt)
                F_volcanic = np.zeros(nt)
                natural = np.zeros((nt, 2))
                F_solar[:346] = args["F_solar"][15:]
                F_volcanic[:346] = args["F_volcanic"][15:]
                natural[:346, :] = args["natural"][15:, :]
                natural[346:, :] = args["natural"][
                    -1, :
                ]  # hold the last element constant for the rest of the array
            elif emiss.shape[0] == 751:
                reference_year = 1750

                nt = 751 
                F_solar = np.zeros(nt)
                F_volcanic = np.zeros(nt)
                natural = np.zeros((nt, 2))
                F_solar[:361] = args["F_solar"]
                F_volcanic[:361] = args["F_volcanic"]
                natural[:361, :] = args["natural"]
                natural[361:, :] = args["natural"][
                    -1, :
                ]  # hold the last element constant for the rest of the array
            else:
                nt = emiss.shape[0] # assume time length is same as input emissions. assume no change in ref year
                argslength = args["F_solar"].shape[0] # assume solar, volc, natural have same time dim
                
                # assuming solar/volc/nat have same start year as emiss
                if argslength < nt:
                    F_solar = np.zeros(nt)
                    F_volcanic = np.zeros(nt)
                    natural = np.zeros((nt, 2))
                    F_solar[:nt] = args["F_solar"]
                    F_volcanic[:nt] = args["F_volcanic"]
                    natural[:361, :] = args["natural"]
                    natural[361:, :] = args["natural"][
                                    -1, :
                                ]  
                    # do something to add solar/volc/nat to inputs
                elif argslength > nt:
                    # do something to chop off end of solar/volc/nat args
                    F_solar = np.zeros(nt)
                    F_volcanic = np.zeros(nt)
                    natural = np.zeros((nt, 2))
                    F_solar[:nt] = args["F_solar"]
                    F_volcanic[:nt] = args["F_volcanic"]
                    natural[:nt, :] = args["natural"]
                else: 
                    # they are equal, just set them directly
                    F_solar = np.zeros(nt)
                    F_volcanic = np.zeros(nt)
                    natural = np.zeros((nt, 2))
                    F_solar[:nt] = args["F_solar"]
                    F_volcanic[:nt] = args["F_volcanic"]
                    natural[:nt, :] = args["natural"]

            C, F, T, ariaci, lambda_eff, ohc, heatflux = fair.forward.fair_scm(
                emissions=emiss,
                emissions_driven=True,
                C_pi=args["C_pi"].values,  
                natural=natural,
                F_volcanic=F_volcanic,  
                F_solar=F_solar,
                F2x=args["F2x"].values,
                r0=args["r0"].values,
                rt=args["rt"].values,
                rc=args["rc"].values,
                ariaci_out=True,
                ghg_forcing="Meinshausen",
                scale=np.asarray(args["scale"].values),
                aerosol_forcing="aerocom+ghan2",
                b_aero=np.asarray(args["b_aero"].values),
                ghan_params=np.asarray(args["ghan_params"].values),
                tropO3_forcing="thorhnill+skeie", 
                ozone_feedback=args["ozone_feedback"].values,
                b_tro3=np.array(args["b_tro3"].values),
                E_pi=emiss[0, :],
                scaleAerosolAR5=False,
                scaleHistoricalAR5=False,
                fixPre1850RCP=False,
                aviNOx_frac=0,
                aCO2land=args["aCO2land"].values,
                stwv_from_ch4=args["stwv_from_ch4"].values,
                F_ref_BC=args["F_ref_BC"].values,
                E_ref_BC=args["E_ref_BC"].values,
                efficacy=np.ones(45),
                diagnostics="AR6",
                temperature_function="Geoffroy",
                lambda_global=args[
                    "lambda_global"
                ].values,  # this and the below only used in two-layer model
                deep_ocean_efficacy=args["deep_ocean_efficacy"].values,
                ocean_heat_capacity=np.asarray(args["ocean_heat_capacity"].values),
                ocean_heat_exchange=args["ocean_heat_exchange"].values,
            )

            return C, F, T, ariaci, lambda_eff, ohc, heatflux
    
    def run(self, emissda, simid=None, emissions_driven=True, useMultigas=True):#, return_xr=True):
        """
            Run installed version of FaIR (so far tested on FaIR v1.*) in emissions-driven mode.

            Parameters
            ----------
            emiss : scmwrap.types.Emissions
                xarray DataArray of emissions with dims [year x gas] where shape is [nt x 40].
            args : scmwrap.types.ClimateParams, optional
                Contains climate parameters. If `None`, run with default FaIR settings.
            useMultigas : bool, optional
                specifies whether to run FaIR in CO2-only (False) or multi-gas (True) mode.

            Returns
            -------
            xarray.Dataset

        """

        if not emissions_driven:
            raise NotImplementedError("concentration-driven is not implemented yet")
            
        if simid is not None:
            self.simid = simid
            
        ## TODO add validate func to enforce the order of gas dimension of the emissions object
        emiss = emissda.copy()
        
        # default time dimensions for different versions of FaIR v1.*
        # TODO check if other time dimensions work
        if emiss.shape[0] == 736:
            reference_year = 1765   
        elif emiss.shape[0] == 751:
            reference_year = 1750
        else:
            reference_year = 1750
            #raise NotImplementedError("emissions time dimension is not recognized")

        ret = self._run(emiss=emiss.values, 
                        useMultigas=useMultigas)

        # Prep the FaIR outputs into xarray objects

        # TODO generalize the years
        years = np.arange(reference_year, 2501)  # gets range of years in desired period
        gases = (
            self.get_list_of_concentration_gases()
        )  # gets list of gases names from this function defined above

        # TODO generalize somehow?
        if len(ret) == 3:
            C,F,T = ret
        elif len(ret) == 7:
            C, F, T, ariaci, lambda_eff, ohc, heatflux = ret
        else:
            raise NotImplementedError(f"FaIR output unrecognized. Expecting length of 3 or 7, got {len(ret)}")

        if useMultigas:
            C_xarray = xr.DataArray(
                C, dims=["year", "gas"], coords=[years, gases], name="concentration"
            )
            F_xarray = xr.DataArray(
                F,
                dims=["year", "forcing_type"],
                coords=[years, np.arange(0, F.shape[1])],
                name="forcing",
            )
        else:
            C_xarray = xr.DataArray(
                C, dims=["year",], coords=[years,], name="concentration"
            )
            F_xarray = xr.DataArray(
                F,
                dims=["year",],
                coords=[years,],
                name="forcing",
            )

        T_xarray = xr.DataArray(
            T,
            dims=[
                "year",
            ],
            coords=[years],
            name="temperature",
        )
        response_ds = xr.merge(
            [C_xarray, F_xarray, T_xarray]
        )
        response_ds["simulation"] = self.simid
        
        # TODO Add attributes

        return response_ds


    def get_test_emissions(self):
        # TODO update the test emissions data. CMIP5 emissions don't go well with CMIP6 params
        import pandas as pd
        import pkg_resources
        
        fn = pkg_resources.resource_filename("scmcoat","testdata/rcp45emissions.csv")

        return pd.read_csv(fn)
    
    def get_cmip_scenario_emissions(self, scenario, cmipera=5):
        # TODO: this is untested so far. Test it.
        # TODO: add all CMIP scenarios
        import fair
        
        if fair.__version__ > 1.7:
            print(fair.__version__)
        else:
            if cmipera!=5:
                raise NotImplementedError(
                    f"only CMIP5 is supported with FaIR version <2.0. Got CMIP{cmipera}")# TODO
                
            if scenario=="rcp45":
                from fair.RCPs import rcp45
                return rcp45.Emissions
            elif scenario=="rcp85":
                from fair.RCPs import rcp85
                return rcp85.Emissions
            else:
                raise NotImplementedError("only rcp45, rcp85 for CMIP5 are implemented")#TODO
        
    
    def test_run(self):
        
        emiss = self.get_test_emissions()
        
        return self._run(emiss.values)
    
