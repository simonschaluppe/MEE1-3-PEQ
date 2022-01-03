# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 13:10:17 2021

@author: Simon
"""

import numpy as np
import pvlib

DEFAULT_MODULE = "LG_Electronics_Inc__LG320N1C_G4" #must be in pvlib module database
DEFAULT_INVERTER = "Fronius_International_GmbH__Fronius_Primo_10_0_1_208_240__240V_" #3 strings á 12 modules = 36 modules ~ 10 kWp

class PV:
    """
    PV Profile with .TSD in [kWh per hour]
    """

    def __init__(self, csv, kWp, cost_kWp=1500):

        self.TSD_source = np.genfromtxt(csv)
        self.path = csv
        self.source_kWp = kWp
        self.cost_kWp = cost_kWp # cost per kWh

        self.set_kWp(kWp)

    def set_kWp(self, kWp):

        self.TSD = self.TSD_source / self.source_kWp * kWp
        self.kWp = kWp
        self.cost = kWp * self.cost_kWp

    def __repr__(self):
        width = len(self.path)+10
        return f"""PV-System {self.path}
{"-"*width}
kWp: {self.kWp:>{width-5}d}
kWh/a: {self.TSD.sum():>{width-7}.0f}
cost [€]: {self.cost:>{width-10}d}"""

def from_pvlib():

    # Define the PV Module and the Inverter from the CEC databases (For example, the first entry of the databases)
    cec_mod_db = pvlib.pvsystem.retrieve_sam("cecmod")
    module_data = cec_mod_db[DEFAULT_MODULE]

    temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']

    # Define the basics of the class PVSystem
    inverter_data = invdb.iloc[:, np.random.randint(0, high=len(invdb))]
    system = pvlib.pvsystem.PVSystem(surface_tilt=0, surface_azimuth=180,
                                     module_parameters=module_data,
                                     inverter_parameters=inverter_data,
                                     temperature_model_parameters=temperature_model_parameters)
    # Creation of the ModelChain object
    """ The example does not consider AOI losses nor irradiance spectral losses"""
    mc = pvlib.modelchain.ModelChain(system, location,
                                     aoi_model='no_loss',
                                     spectral_model='no_loss',
                                     name='AssessingSolar_PV')


if __name__ == "__main__":
    test = PV(csv="../../data/pv_1kWp.csv",
              kWp=1)
    import matplotlib.pyplot as plt
    plt.plot(test.TSD)
    plt.show()
