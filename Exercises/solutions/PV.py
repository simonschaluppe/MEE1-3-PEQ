# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 13:10:17 2021

@author: Simon
"""

import numpy as np


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


if __name__ == "__main__":
    test = PV(csv="../../data/pv_1kWp.csv",
              kWp=1)
    import matplotlib.pyplot as plt
    plt.plot(test.TSD)
    plt.show()
