

class Battery:
    """a Simplistic Battery"""
    def __init__(self, kWh):
        self.capacity = kWh # kWh
        self.charge_power_max = 10 # kW
        self.discharge_power_max = 10 # kW
        self.charge_efficiency = 0.97
        self.discharge_efficiency = 0.97
        self.discharge_per_hour = 0.00012
        self.cost_kWh = 1000
        self.cost = self.capacity * self.cost_kWh
        self.SoC = 0. #kWh State of Charge

    def charge(self, kW):
        """
        takes a desired charge in kW (kWh for an hour),
        calculates the accepted energy, change the current_charge of the Battery
        and returns the actually accepted energy
        """

        # your code here...

        return accepted_energy

    def discharge(self, kW:float):
        """
        takes a desired discharge in kW (kWh for an hour),
        calculates the actual dischargebale energy, change the current_charge of the Battery
        and returns the actually discharged energy
        """

        # your code here...
        return discharged_energy * self.discharge_efficiency
