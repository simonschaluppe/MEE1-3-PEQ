# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 13:10:17 2021

@author: Simon
"""
from pathlib import Path

import numpy as np
import pvlib

DEFAULT_MODULE = "LG_Electronics_Inc__LG320N1C_G4" #must be in pvlib module database
DEFAULT_INVERTER = "Fronius_International_GmbH__Fronius_Primo_10_0_1_208_240__240V_" #3 strings á 12 modules = 36 modules ~ 10 kWp

class PV:
    """
    PV Profile with .TSD in [kWh per hour]
    """

    def __init__(self, csv=None, kWp=1., cost_kWp=1500, array=None):

        if array is not None:
            self.TSD_source = np.array(array)
            self.path = "Directly from Array input"
        elif csv is not None:
            self.TSD_source = np.genfromtxt(csv)
            self.path = csv
        else:
            raise ValueError("Missing Source: Either 'csv' or 'array' argument must be supplied!")
        self.source_kWp = kWp
        self.cost_kWp = cost_kWp # cost per kWh

        self.set_kWp(kWp)

    def set_kWp(self, kWp):

        self.TSD = self.TSD_source / self.source_kWp * kWp
        self.kWp = kWp
        self.cost = kWp * self.cost_kWp

    def __repr__(self):
        width = len(self.path)+10
        return f"""PV-System {str(self.path)}
{"-"*width}
kWp: {self.kWp:>{width-5}.1f}
kWh/a: {self.TSD.sum():>{width-7}.0f}
cost [€]: {self.cost:>{width-10}.0f}"""

    def save(self, folder="../../data", filename=None):
        if filename is None:
            filename = f"Generic_{self.kWp:.0f}kWp.csv"
        np.savetxt(Path(folder, filename),self.TSD)

def from_pvlib():

    # Define the PV Module and the Inverter from the CEC databases (For example, the first entry of the databases)
    cec_mod_db = pvlib.pvsystem.retrieve_sam("cecmod")
    module_data = cec_mod_db[DEFAULT_MODULE]

    temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']

    invdb = pvlib.pvsystem.retrieve_sam('CECInverter')
    iv = invdb[DEFAULT_INVERTER]


    # Define the basics of the class PVSystem
    system_kwargs = dict(
        module_parameters=module_data,
        temperature_model_parameters=temperature_model_parameters
    )
    arrays = [
        pvlib.pvsystem.Array(pvlib.pvsystem.FixedMount(30, 180),
                             modules_per_string=10, strings=3,
                             name='test',
                             **system_kwargs),
        #can add more arrays
    ]

    system = pvlib.pvsystem.PVSystem(arrays=arrays,
                                     inverter_parameters=iv, )


    latitude, longitude = 48.27, 16.43
    altitude = 160
    location = pvlib.location.Location(latitude, longitude, altitude=altitude)

    # Creation of the ModelChain object
    #""" The example does not consider irradiance spectral losses"""
    mc = pvlib.modelchain.ModelChain(system, location,
                                     aoi_model='physical',
                                     spectral_model='no_loss',
                                     name='test')

    weather = pvlib.iotools.read_tmy3("../../data/weather/Wien-Hohe_Warte-hour.csv")
    df_weather = weather[0]
    rename = {
        "GHI": "ghi",
        "DHI": "dhi",
        "DNI": "dni",
        "DryBulb": "temp_air",
        "Wspd": "wind_speed"
    }
    df_weather.rename(columns=rename, inplace=True)
    mc.run_model(df_weather)
    return PV(array=np.array(mc.results.ac/1000), kWp=(30*0.32))

if __name__ == "__main__":
    test = PV(csv="../../data/pv_1kWp.csv",
              kWp=1)
    import matplotlib.pyplot as plt
    # plt.plot(test.TSD)
    # plt.show()
    t2 = from_pvlib()
