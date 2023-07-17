# scmcoat : Simple Climate Model wrapper

Wrapper tool to run simple climate models with CIL settings and climate uncertainty.

SCMs included and tested:
- FaIR v1.*

[FaIR](https://github.com/OMS-NetZero/FAIR/tree/v1.6.4) accepts an array of greenhouse gas emissions and prognostically predicts atmospheric concentrations, change in radiative forcings, and change in global mean temperature, and other variables under certain settings. We frequently run this model under very specific settings and this package is meant to ease that process.

This package is very new. This may change in breaking ways.

## Inputs
Emissions inputs to FaIR are a specific format. FaIR v1.* expects 39-species of GHGs if run in `MultiGas` mode.

Demo emissions (see code example below) are a dataframe with dimensions Year x Gas. Note that there are *40* columns and the first column is "year", the rest are gases. 
```
The columns:
Index(['year', 'CO2_Fossil', 'CO2_Land', 'CH4', 'N2O', 'SOx', 'CO', 'NMVOC',
       'NOx', 'BC', 'OC', 'NH3', 'CF4', 'C2F6', 'C6F14', 'HFC23', 'HFC32',
       'HFC4310mee', 'HFC125', 'HFC134a', 'HFC143a', 'HFC227ea', 'HFC245fa',
       'SF6', 'CFC11', 'CFC12', 'CFC113', 'CFC114', 'CFC115', 'CARB_TET',
       'MCF', 'HCFC22', 'HCFC141b', 'HCFC142b', 'Halon1211', 'Halon1202',
       'Halon1301', 'Halon2402', 'CH3Br', 'CH3Cl'],
      dtype='object')
# the index:      
RangeIndex(start=0, stop=736, step=1) # here year runs from 1765-2500
```

Demo emissions are RCP4.5 from the CMIP5 era (adapted from these emissions from FaIR: 
```python
import fair
from fair.RCPs import rcp45

emissions = rcp45.Emissions.emissions # numpy array
```
FairModel.run() will also accept emissions that are an xarray.DataArray with coords that match the dataframe described above. E.g. a 40-element `gas` dimension and a 736- or 751-element `year` dimension.


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
### Run v1.* FaIR with demo emissions (CMIP5 RCP4.5)

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

### Run v1.* FaIR with demo emissions (CMIP5 RCP4.5) and climate parameters
When `FairModel.run()` is called, the argument,`simid`, specifies how to use the climate parameters. The `simid` default value is "default". If `ClimateParams` have not been set and `simid` is "default", then FairModel is run with FaIR's default settings (see above example). If `ClimateParams` have been set but `simid` is "default", then FairModel will be run with "median" climate parameters. If `ClimateParams` are set, then `simid` can be set to "median" or a scalar integer index of the climate parameters.
```python

import scmcoat as sc

# initialize the model
fm = sc.core.FairModel(
       sc.core.ClimateParams(xr.open_dataset(params_filepath))
       )

# Open up the test emissions to use as a demo
emissions = fm.get_test_emissions()

# run FaIR with these emissions and median climate parameters
response = fm.run(emissions, simid="median")  # an xr.Dataset

response.temperature.plot()

# the model can be run with differen climate parameters
response2 = fm.run(emissions, simid=150)

_ = xr.concat([response,response2], dim="simulation").temperature.plot.line(x="year")

```

FaIR can run any emissions pathway in this format, although may become unstable under radically different emissions. Note this has not been tested with different length time series of emissions.
