# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 13:10:17 2021

@author: Simon
"""

class Storage:
    pass


class PV:
    """
    PV Profile with .TSD in [kWh per hour]
    """
    def __init__(self, csv="data/pv_1kWp.csv", kWp=1, cost_kWp=1500):
        print("initializing PV Object")
        # your code here

    def set_kWp(self, kWp):
        print("setting TSD, cost and kWp to reflect", kWp, "kWp")
        # your code here


