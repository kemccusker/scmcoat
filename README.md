# scmcoat : Simple Climate Model wrapper

Wrapper tool to run simple climate models with CIL settings and climate uncertainty.

SCMs included and tested:
- FaIR v1.*

[FaIR](https://github.com/OMS-NetZero/FAIR/tree/v1.6.4) accepts an array of greenhouse gas emissions and prognostically predicts atmospheric concentrations, change in radiative forcings, and change in global mean temperature, and other variables under certain settings. We frequently run this model under very specific settings and this package is meant to ease that process.

This package is very new. This may change in breaking ways.

## Inputs
Emissions inputs to FaIR are a specific format. FaIR v1.* expects 39-species of GHGs if run in `MultiGas` mode.

Demo emissions (see code example below) are an `xarray.DataArray` with dimensions `year` x `gas`. Note that there are *40* elements in `gas`: the first element is "year", and the rest are gases. 
```
The `gas` coordinate:
array(['year', 'CO2_Fossil', 'CO2_Land', 'CH4', 'N2O', 'SOx', 'CO', 'NMVOC',
       'NOx', 'BC', 'OC', 'NH3', 'CF4', 'C2F6', 'C6F14', 'HFC23', 'HFC32',
       'HFC4310mee', 'HFC125', 'HFC134a', 'HFC143a', 'HFC227ea', 'HFC245fa',
       'SF6', 'CFC11', 'CFC12', 'CFC113', 'CFC114', 'CFC115', 'CARB_TET',
       'MCF', 'HCFC22', 'HCFC141b', 'HCFC142b', 'Halon1211', 'Halon1202',
       'Halon1301', 'Halon2402', 'CH3Br', 'CH3Cl'], dtype='<U10')
The `year` coordinate:      
array([1765., 1766., 1767., ..., 2498., 2499., 2500.]) # year runs from 1765-2500 or 1751-2500 
```
TODO: add more detail about year coord

Demo emissions are SSP2-4.5 from the CMIP6 era. Standardized CMIP6 emissions can be obtained like: 
```python
import scmcoat as sc

# demo emissions
emissions = sc.get_test_emissions() # returns xr.DataArray of SSP2-4.5

# or get any CMIP6 emissions pathway
emissions = sc.utils.rcmip_emissions("ssp370") # returns xr.DataArray

```
FairModel.run() will also accept emissions that are `pandas.DataFrame` with columns that match the `gas` coord and index that matches `year`, as described above. E.g. a 40-element `gas` dimension and a 736- or 751-element `year` dimension.


## Outputs
FaIR outputs are returned as an `xarray.Dataset` with the following `data_vars`:
```
Data variables:
    concentration  (year, gas) float64 278.0 722.0 273.0 ... 13.22 620.6
    forcing        (year, forcing_type) float64 2.623e-05 0.0 0.0 ... 0.0 0.0
    temperature    (year) float64 0.005061 0.009262 0.01363 ... 3.244 3.245
    simulation     () <U7 'default'
```
Here a `simulation` equal to "default" indicates it's not running an ensemble of simulations with climate parameters but rather is running with default FaIR settings.


## Examples: 
### Run v1.* FaIR with demo emissions (CMIP6 SSP2-4.5)

```python

import scmcoat as sc

# initialize the model
fm = sc.FairModel()

# Open up the test emissions to use as a demo
emissions = fm.get_test_emissions()

# run FaIR with these emissions under its default settings
response = fm.run(emissions)  # an xr.Dataset

response.temperature.plot()

```
OR
```python

import scmcoat as sc

# initialize the model
fm = sc.FairModel()

# run FaIR with test emissions under its default settings
response = fm.test_run()  # an xr.Dataset

response.temperature.plot()

```

### Run v1.* FaIR with demo emissions (CMIP6 SSP2-4.5) and climate parameters
When `FairModel.run()` is called, the argument,`simid`, specifies how to use the climate parameters. The `simid` default value is "default". 
- If `ClimateParams` _have not_ been set and `simid` is "default", then FairModel is run with FaIR's default settings (see above example).
- If `ClimateParams` _have_ been set but `simid` is "default", then FairModel will be run with "median" climate parameters. This is our usual "point estimate" setup.
- If `ClimateParams` _have_ been set, then `simid` can be set to "median" or a scalar integer that indexes the climate parameters.
```python

import scmcoat as sc

params_filepath = "<path_to_params_file.nc>" # TODO add pointer to the file or add to repo

# set up ClimateParams
cp = sc.core.ClimateParams(params=xr.open_dataset(params_filepath))

# initialize the model with climate parameters
fm = sc.core.FairModel(cp)

# Open up the test emissions to use as a demo
emissions = fm.get_test_emissions()

# run FaIR with these emissions and median climate parameters
response = fm.run(emissions, simid="median")  # an xr.Dataset

response.temperature.plot()

# the model can be run with different climate parameters
response2 = fm.run(emissions, simid=150)

_ = xr.concat([response,response2], dim="simulation").temperature.plot.line(x="year")

```

FaIR can run any emissions pathway in this format, although may become unstable under radically different emissions. Note this has not been tested with different length time series of emissions and will likely throw errors.
