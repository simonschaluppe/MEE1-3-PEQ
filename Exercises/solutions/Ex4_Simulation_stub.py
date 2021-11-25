
import numpy as np
import pandas as pd

from Building import Building

class Model:

    def __init__(self):
        print("initializing Model ...")
        self.building = Building()
        self.usage = pd.read_csv("../../data/usage_profiles.csv", encoding="cp1252", delimiter=",")

        self.TA = np.genfromtxt("../../data/climate.csv", delimiter=";")[1:,1]
        ## add solar gains,
        ## add missing stuff

    def init_sim(self):
        print("initiliazing simulation run ...")

        self.cp_air = 0.34  # spez. Wärme kapazität Luft (Wh/m3K)
        self.QI_winter = self.usage["Qi Winter W/m²"].to_numpy()
        self.ACH_V = self.usage["Luftwechsel_Anlage_1_h"].to_numpy()
        self.ACH_I = self.usage["Luftwechsel_Infiltration_1_h"].to_numpy()

        self.Q_loss = np.zeros(8760)
        self.QV = np.zeros(8760)
        self.QT = np.zeros(8760)
        self.TI = np.ones(8760) * 20

    def simulate(self):
        print("starting simulation ...")
        self.init_sim()

        for t in range(1,8760):
            #print("simulation timestep", t)
            self.calc_QV(t)
            self.calc_QT(t)
            self.handle_losses(t)

            #Heating
            self.handle_heating(t)
            # Cooling
            self.handle_cooling(t)


        print("simulation completed successfully!")
        return 0

    def calc_QV(self, t):
        """calculates Heatlosses from ventilation"""
        dT =  self.TA[t-1] - self.TI[t-1]
        self.QV[t] = dT * (self.ACH_V[t] + self.ACH_I[t]) * self.building.net_storey_height * self.cp_air # W/m²  = W/m²

    def calc_QT(self, t):
        pass

    def handle_losses(self, t):
        self.Q_loss[t] = self.QV[t] + self.QT[t]

    def handle_heating(self, t):
        pass

    def handle_cooling(self, t):
        pass



if __name__ == "__main__":
    import matplotlib.pyplot as plt
    print("testing Simulation.py")
    test = Model()
    test.simulate()
    plt.plot(test.Q_loss)
    plt.show()
    print(test.building)
