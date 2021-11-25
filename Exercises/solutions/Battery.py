

class Battery:
    """a Simple Battery"""
    def __init__(self, kWh):
        self.capacity = kWh # kWh
        self.charge_power_max = 10 # kW
        self.discharge_power_max = 10 # kW
        self.charge_efficiency = 0.9
        self.discharge_efficiency = 0.9
        self.discharge_per_hour = 0.00012
        self.cost_kWh = 1000 # cost per kWh
        self.cost = self.capacity * self.cost_kWh
        self.SoC = 0. #kWh State of Charge

    def charge(self, kW):
        """
        takes a desired charge in kW (kWh for an hour),
        calculates the accepted energy, change the current_charge of the Battery
        and returns the actually accepted energy
        """
        max_charge = (self.capacity - self.SoC) / self.charge_efficiency
        accepted_energy = min(kW, self.charge_power_max, max_charge)
        self.SoC += accepted_energy * self.charge_efficiency
        return accepted_energy

    def discharge(self, kW:float):
        """
        takes a desired discharge in kW (kWh for an hour),
        calculates the actual dischargebale energy, change the current_charge of the Battery
        and returns the actually discharged energy
        """
        max_discharge = min(self.discharge_power_max, self.SoC)
        desired_discharge = kW / self.discharge_efficiency
        discharged_energy = min(desired_discharge, max_discharge)
        self.SoC -= discharged_energy
        return discharged_energy * self.discharge_efficiency
