# from scmcoat.core import ClimateParams

# from dataclasses import dataclass
# from typing import Protocol
# from xarray import Dataset, DataArray
# from pandas import DataFrame

# ClimateResponse = Dataset

# TODO: how to enforce a specific format for Emissions?
# Emissions = DataArray# note can be year x gas or just year @@@



# @dataclass # @@@ can this be a dataclass and a Protocol??
# class Emissions():#Protocol? can't be instantiated
#     emissions: DataArray # note can be year x gas or just year @@@
    
#     def get_list_of_gases(self) -> list:
#         """
#         returns list of emissions gases in correct order
#         """

# class ClimateModel(Protocol):
#     def run(self, x: DataFrame, y: ClimateParams) -> ClimateResponse:
#         """
#         A ClimateModel can project change in global mean surface temp given GHG emissions
#         """

#     # TODO add inverse run