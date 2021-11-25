import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


from Building import Building
from Ex5_PV_stub import PV
from Ex7_Battery_stub import Battery

class HVAC:
    """HVAC parameters"""
    heating_system = True
    heating_months = [1,2,3,4,9,10,11,12] # specify which months should the heating be useed
    minimum_room_temperature = 20.

    HP_COP = 5 # use this static cop to calc ED = QH / cop
    HP_heating_power = 20 #W/m² however, electric heating power cannot exceed this
    heating_eff = 0.95  # Wirkungsgrad Verteilverluste:
                        # fraction of HP heat generation reaching the room
                        # to supply heat demand

    cooling_system = True
    cooling_months = [4,5,6,7,8,9]
    maximum_room_temperature = 26.

    # use COP,power and efficiency from heating also for cooling

class Model:
    simulated = [] # this is not strictly neccessary
    # it uses a class variable to save
    # all simulated instances of a model
    # they get recorded at the end of the
    # Model.simulate() method

    def __init__(self,
                 building_path="data/building_oib_16linie.xlsx",
                 kWp=1, # PV kWp
                 battery_kWh=1): # Battery kWh

        ###### Compononets #####
        # (Other classes and parts, that form the model)
        self.building = Building(path=building_path)
        self.HVAC = HVAC()

        self.PV = PV(csv="data/pv_1kWp.csv", kWp=1)
        self.PV.set_kWp(kWp)

        self.battery = Battery(kWh=battery_kWh)

        ###### Parameters #####
        self.cp_air = 0.34  # spez. Wärme kapazität Luft (Wh/m3K)

        self.price_grid = 0.19      # €/kWh
        self.price_feedin = 0.05    # €/kWh

        ###### Timeseries #####
        # load Usage characteristics
        self.Usage = pd.read_csv("data/usage_profiles.csv", encoding="cp1252")

        # load climate data
        self.TA = np.genfromtxt("data/climate.csv",
                                delimiter=";")[1:, 1]
        # load solar gains
        self.QS = np.genfromtxt("data/Solar_gains.csv") # W/m²

    def init_sim(self):
        # (re)load profiles from self.Usage
        #this is neccessary  if the PV model has changed inbetween simulations
        self.QI_winter = self.Usage["Qi Winter W/m²"].to_numpy()
        self.QI_summer = self.Usage["Qi Sommer W/m²"].to_numpy()

        self.ACH_V = self.Usage["Luftwechsel_Anlage_1_h"].to_numpy()
        self.ACH_I = self.Usage["Luftwechsel_Infiltration_1_h"].to_numpy()
        self.Qdhw = self.Usage["Warmwasserbedarf_W_m2"].to_numpy()
        self.ED_user = self.Usage["Nutzerstrom_W_m2"].to_numpy()

        # (re)load PV profiles
        #this is neccessary  if the PV model has changed inbetween simulations
        self.PV_prod = self.PV.TSD *1000 / self.building.bgf  # everything is in Wh/m²
        self.PV_use = np.zeros(8760)
        self.PV_feedin = np.zeros(8760)
        self.PV_to_battery = np.zeros(8760)

        # initialize result arrays
        self.timestamp = pd.Series(np.arange('2020-01-01 00:00', '2021-01-01 00:00', dtype='datetime64[h]'))

        self.QV = np.zeros(8760) # ventilation losses
        self.QT = np.zeros(8760) # transmission losses
        self.QI = np.zeros(8760) #  Internal losses
        self.Q_loss = np.zeros(8760) # total losses without heating/cooling

        self.TI = np.zeros(8760) # indoor temperature

        self.QH = np.zeros(8760) # Heating demand Wh/m²
        self.QC =  np.zeros(8760) # Cooling demand Wh/m²

            # Energy demands
        self.ED_QH = np.zeros(8760)# Electricity demand for heating Wh/m²
        self.ED_QC = np.zeros(8760)  # Electricity demand for cooling Wh/m²
        #self.ED_Qdhw = 0
        self.ED = np.zeros(8760) # Electricity demand Wh/m²
        self.ED_grid = np.zeros(8760)


        self.Btt_to_ED = np.zeros(8760)

        ## initialize starting conditions
        self.TI[0] = self.HVAC.minimum_room_temperature

    def calc_QV(self, t):
        """Ventilation heat losses [W/m²BGF] at timestep t"""
        dT = self.TA[t - 1] - self.TI[t - 1]
        room_height = self.building.net_storey_height
        cp_air = self.cp_air
        # thermally effective air change
        eff_airchange = self.ACH_I[t] + self.ACH_V[t]  # * M.VentilationSystem.share_cs * rel_ACH_after_heat_recovery

        self.QV[t] = eff_airchange * room_height * cp_air * dT

    def calc_QT(self, t):
        """Transmission heat losses [W/m²BGF] at timestep t"""
        dT = self.TA[t - 1] - self.TI[t - 1]
        self.QT[t] = self.building.LT * dT

    def calc_QI(self, t):
        heat = self.timestamp[t].month in self.HVAC.heating_months
        cool = self.timestamp[t].month in self.HVAC.cooling_months
        if (heat and cool) or (not heat and not cool): # wenn beides oder keinss von beiden, mittelwert
            self.QI[t] = (self.QI_winter[t] + self.QI_summer[t])/ 2
        elif heat:
            self.QI[t] = self.QI_winter[t]
        elif cool:
            self.QI[t] = self.QI_summer[t]
        else:
            raise NotImplementedError("Case not defined!")

    def handle_losses(self, t):
        # determine losses
        self.Q_loss[t] = (self.QT[t] + self.QV[t]) + self.QS[t] + self.QI[t]
        # determine indoor temperature after losses
        self.TI[t] = self.TI_after_Q(self.TI[t - 1], self.Q_loss[t], self.building.heat_capacity)

    def TI_after_Q(self, TI_before, Q, cp):
        """cp = spec. building heat_capacity"""
        return TI_before + Q / cp

    def is_heating_on(self, t, TI_new):
        if self.HVAC.heating_system == True:
            if self.timestamp[t].month in self.HVAC.heating_months:
                if TI_new < self.HVAC.minimum_room_temperature:
                    return True
        return False

    def is_cooling_on(self, t, TI_new):
        """
        Determines, whether all conditions are met to use cooling
        """
        c1 = self.HVAC.cooling_system == True
        c2 = self.timestamp[t].month in self.HVAC.cooling_months
        c3 = TI_new > self.HVAC.maximum_room_temperature
        return all([c1, c2,
                    c3])  # returns True if all conditions are true, False otherwise. similarly, any(). You can stack this way more cleanly

    def minimum_Q(self, TI, set_min, set_max, cp):
        """calculates the minimum Q (positive or negative) to reach the setpoint targets"""
        if TI < set_min:
            return (set_min - TI) * cp
        if TI > set_max:
            return (set_max - TI) * cp
        else:
            return 0.

    def handle_heating(self, t):
        """Handles the use of a heating system, applies changes to self.QH, self.ED_QH, self.TI if neccessary"""
        TI = self.TI[t]
        if self.is_heating_on(t, TI):
            required_QH = self.minimum_Q(TI=TI,
                                         set_min=self.HVAC.minimum_room_temperature,
                                         set_max=self.HVAC.maximum_room_temperature,
                                         cp=self.building.heat_capacity)
            required_ED = required_QH / self.HVAC.HP_COP / self.HVAC.heating_eff
            available_power = self.HVAC.HP_heating_power
            self.ED_QH[t] = min(required_ED, available_power)
            self.QH[t] = self.ED_QH[t] * self.HVAC.HP_COP * self.HVAC.heating_eff
            self.TI[t] = self.TI_after_Q(TI, self.QH[t], self.building.heat_capacity)

    def handle_cooling(self, t):
        """Handles the use of a heating system, applies changes to self.QH, self.ED_QH, self.TI if neccessary"""
        TI = self.TI[t]
        if self.is_cooling_on(t, TI):
            required_QC = self.minimum_Q(TI=TI,
                                         set_min=self.HVAC.minimum_room_temperature,
                                         set_max=self.HVAC.maximum_room_temperature,
                                         cp=self.building.heat_capacity)
            required_ED = - required_QC / self.HVAC.HP_COP / self.HVAC.heating_eff
            available_power = self.HVAC.HP_heating_power
            self.ED_QC[t] = min(required_ED, available_power)
            self.QC[t] = - self.ED_QC[t] * self.HVAC.HP_COP * self.HVAC.heating_eff
            self.TI[t] = self.TI_after_Q(TI, self.QC[t], self.building.heat_capacity)

    def calc_ED(self, t):
        self.ED[t] = self.ED_QH[t] + self.ED_QC[t] + self.ED_user[t]

    def handle_PV(self, t):
        """allocates the PV to direct and  battery charge use"""
        #calculate the direct Use of PV
        self.PV_use[t] = min(self.PV_prod[t], self.ED[t])
        remain = self.PV_prod[t] - self.PV_use[t]

        #calculate the remaining PV to Battery
        self.PV_to_battery[t] = self.battery.charge(remain * self.building.bgf / 1000) * 1000 / self.building.bgf
        remain = remain - self.PV_to_battery[t]
        #calculate the remaining PV to Battery
        self.PV_feedin[t] = max(remain - self.ED[t], 0)

    def handle_grid(self, t):
        """calculate the remaining grid demand: Total Energy demand [ED] - PVuse - Battery_discharge"""
        self.ED_grid[t] = self.ED[t] - self.PV_use[t] - self.Btt_to_ED[t]

    def handle_battery(self, t):
        # Lower SoC by hourly losses
        self.battery.SoC = (1 - self.battery.discharge_per_hour) \
                           * self.battery.SoC

        # calculate remaining electricity demand not covered after PV use for time t
        remaining_ED = (self.ED[t] - self.PV_use[t]) * self.building.bgf / 1000 #kW not W/m²
        # conditions
        # if remaining energy demand > 0 AND battery.SoC > 0
        c1 = (remaining_ED > 0)
        c2 = (self.battery.SoC > 0)
        if all([c1, c2]):
            self.Btt_to_ED[t] = self.battery.discharge(remaining_ED)

    def calc_cost(self, years=20, verbose=True):
        """calculates the total cost of the system"""
        # calc investment
        self.investment_cost = self.building.differential_cost * self.building.bgf + self.PV.cost + self.battery.cost
        self.operational_cost = self.building.bgf * (
                                - self.PV_feedin.sum()/1000 * self.price_feedin \
                                + self.ED_grid.sum()/1000 * self.price_grid)


        self.total_cost = self.investment_cost + self.operational_cost * years

        if verbose:
            print(f"Investment cost:  {round(self.investment_cost):>20.2f} €")
            print(f"Operational cost: {round(self.operational_cost):>20.2f} €/annum")
            print(f"Total cost after {years} years: {round(self.total_cost):>11,.2f} €")

        return self.total_cost


    def simulate(self):

        self.init_sim() # don't forget to intialize the first timestep = 0
                        # with sensible starting values
                        # like TI[0] = self.minimum_room_temperature

        for t in range(1, 8760):
            #### Verluste
            self.calc_QV(t)
            self.calc_QT(t)
            self.calc_QI(t)
            self.handle_losses(t)

            #### Heizung
            self.handle_heating(t)

            #### Kühlung
            self.handle_cooling(t)

            #calc total energy demand
            self.calc_ED(t)

            #allocate pv
            self.handle_PV(t)

            # discharge battery
            self.handle_battery(t)

            # handle grid
            self.handle_grid(t)

        self.calc_cost(verbose=False)

        Model.simulated.append(self) # this adds the model result to the base class (optional)
        return True  # the simulate() method does not NEEd to return something
        # but it can be used to check if the simulation ran successfully


    def plot(self, show=True, start=1, end=8760, month=None):
        fig, ax = plt.subplots(2,2)#,figsize=(8,12)) #tight_layout=True)
        ax = ax.flatten()
        self.plot_heat_balance(fig, ax[0], start=start, end=end)
        self.plot_temperatures(fig, ax[1], start=start, end=end)
        self.plot_electricity_demand(fig, ax[2], start=start, end=end)
        self.plot_electricity_use(fig, ax=ax[3], start=start, end=end)

        if show:
            dummy = plt.figure() # create a dummy figure
            new_manager = dummy.canvas.manager  # and use its manager to display "fig"
            new_manager.canvas.figure = fig
            fig.set_canvas(new_manager.canvas)
            fig.show()

    def plot_heat_balance(self, fig=None, ax=None, start=1, end=8760, **kwargs):
        if (fig, ax) == (None, None):
            fig, ax = plt.subplots(1,1)
        self.plot_arrays(ax=ax, start=start, end=end,
                         arrays=[self.QT, self.QV, self.QS, self.QI,
                                 self.QH, self.QC], **kwargs)
        ax.legend(["Transmissionsverluste", "Lüftungsverluste",
                   "Solare Gewinne", "Innere Lasten",
                   "Heizwärmebdedarf", "Kühlbedarf"])
        ax.set_title("Wärmebilanz")
        ax.set_ylabel("W/m²")
        plt.show()

    def plot_temperatures(self, fig=None, ax=None, start=1, end=8760, **kwargs):
        if (fig, ax) == (None, None):
            fig, ax = plt.subplots(1,1)
        self.plot_arrays(ax=ax, start=start, end=end,
                         arrays=[self.TI, self.TA], **kwargs)
        ax.legend(["Innenraum", "Außenluft"])
        ax.set_title("Temperatur")
        ax.set_ylabel("Temperatur [°C]")
        plt.show()

    def plot_electricity_demand(self, fig=None, ax=None, start=1, end=8760, **kwargs):
        # FigureCanvas(fig) # not needed in mpl >= 3.1
        if (fig, ax) == (None, None):
            fig, ax = plt.subplots(1,1)
        self.plot_arrays(ax=ax, start=start, end=end,
                         arrays=[self.PV_prod, self.ED_QH, self.ED_QC, self.ED_user], **kwargs)
        ax.set_title("Strom")
        ax.set_ylabel("W/m²")
        ax.legend(["PV", "WP Heizen", "WP Kühlen", "Nutzerstrom"])
        plt.show()

    def plot_electricity_use(self, fig=None, ax=None, start=1, end=8760, **kwargs):
        """plots the electricity supply and use"""
        if (fig, ax) == (None, None):
            fig, ax = plt.subplots(1, 1)
        self.plot_arrays(ax=ax, start=start, end=end,
                         arrays=[self.PV_use, self.Btt_to_ED, self.ED_grid, self.PV_to_battery,
                                 self.PV_feedin], **kwargs)
        ax.set_title("PV Nutzung")
        ax.set_ylabel("W/m²")
        ax.legend(['PV Eigenverbrauch',
                   'Batterie-Entladung',
                   'Netzstrom',
                   'Batterie-Beladung',
                   'Einspeisung'])
        plt.show()

    def plot_arrays(self, ax, start, end, arrays:list, **kwargs):
        for array in arrays:
            ax.plot(array[start:end], **kwargs)

    def __repr__(self):
            width = len(self.building.file)
            return f"""
Gebäude    {self.building.file}
PV-Anlage  {self.PV.kWp} kWp
Batterie   {self.battery.capacity} kWh
{"-" * (width + 20)}
Heizwärmebedarf (QH):       {self.QH.sum()/1000:>{width - 19}.1f} kWh/m²BGFa
Kühlbedarf (QH):            {-self.QC.sum()/1000:>{width - 19}.1f} kWh/m²BGFa
Strombedarf (ED):           {self.ED.sum()/1000:>{width - 19}.1f} kWh/m²BGFa
PV Eigenverbrauch (PV_use): {self.PV_use.sum()/1000:>{width - 19}.1f} kWh/m²BGFa
Netzstrom (ED_grid):        {self.ED_grid.sum()/1000:>{width - 19}.1f} kWh/m²BGFa
{"-" * (width + 20)}
Investkosten:               {self.investment_cost:>{width - 10}.0f} €
Betriebskosten pro Jahr:        ({self.operational_cost:>{width - 15}.0f} €/a)
Betriebskosten (20 Jahre):  {self.operational_cost*20:>{width - 10}.0f} €
Gesamtkosten:               {self.total_cost:>{width - 10}.0f} €"""


if __name__ == "__main__":
    m = Model(kWp=50, battery_kWh=30)
    m.simulate()
    m.plot()
    print(m) # calls the __repr__() method to print a nice representation of the object
