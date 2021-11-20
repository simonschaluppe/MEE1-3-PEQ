import pandas as pd


DEFAULT_LOADPATH = "../../data/building.xlsx"

class Component:
    """
    A representation of a building component of the thermal hull
    """
    def __init__(self, row):
        self.name = row["Bauteil"]
        self.u_value = row["U-Wert"] # U-Wert [W/m²K]
        self.area = row["Fläche"] # bezugsfläche (Brutto) [m²]
        self.temp_factor = row["Temperatur-Korrekturfaktor"] # Korrekturfaktor, der angibt, wieviel prozent des Wärmeflusses vgl zu gg. Außenwand vorliegt [-]

    @property
    def L(self):
        return self.u_value * self.area * self.temp_factor # = U * A * f_T [W/K]

    def __repr__(self):
        return f"Bauteil {self.name}: {self.area} m²"

class Building:
    """
    A Model of a building
    """
    def __init__(self, path=DEFAULT_LOADPATH, u_f=0.9, fensterfl_anteil=0.4):
        print(f"initializing Building object from {path}")
        # your code here...
        
        self.df = self.load_params(path)
        
        self.bgf = self.df.loc["gross_floor_area", "Value"] # read excel 
        self.heat_capacity = self.df.loc["effective_heat_capacity", "Value"]
        self.net_storey_height = self.df.loc["net_storey_height", "Value"]
        
        self.hull = self.load_hull(path) #from excel
        self.hull = self.insert_windows(u_f=u_f, ff_anteil=fensterfl_anteil)

        self.components = []
        # Außenwand
        # Dach
        # fenster
        # Bodenplatte
        for i, row in self.hull.iterrows():
            bauteil = Component(row)
            self.components.append(bauteil)
        
        self.LT = self.calc_LT()

    def load_params(self, path, sheetname="params"):
        """loads the sheet "params" of a excel at path and returns it as a dataframe"""
        zw = pd.read_excel(path, sheet_name=sheetname)
        zw.index = zw["Variable"]
        return zw

    def load_hull(self, path):
        """loads the sheet "thermal_ hull" of a excel at path and returns it as a dataframe"""
        hull = pd.read_excel(path, sheet_name="thermal_hull")
        return hull # returns a dataframe

    def insert_windows(self, u_f, ff_anteil, bauteil_name="Außenwand (brutto)"):
        """takes a hull dataframe from load_hull() and replaces an opak wall with a wall and a window entry, taking the window share and u-value as inputs"""
        self.hull.index = self.hull["Bauteil"]

        try:
            aw_row = self.hull.loc[bauteil_name]
        except KeyError:
            raise KeyError(f"Bauteil mit Namen {bauteil_name} nicht gefunden")

        aw_A = aw_row["Fläche"]
        aw_Uwert = aw_row["U-Wert"]
        aw_tfaktor = aw_row["Temperatur-Korrekturfaktor"]
        
        aw_opak_A = aw_A * (1-ff_anteil)
        fenster_A = aw_A * ff_anteil 
        
        aw_opak = dict(zip(self.hull.columns,["AW (opak)", aw_opak_A, aw_Uwert, aw_tfaktor]))
        fenster = dict(zip(self.hull.columns,["Fenster", fenster_A, u_f, aw_row["Temperatur-Korrekturfaktor"]]))
        
        self.hull = self.hull.append(aw_opak, ignore_index = True)
        self.hull = self.hull.append(fenster, ignore_index = True)
        self.hull.index = self.hull["Bauteil"]

        self.hull.drop(bauteil_name, inplace=True)
        
        return self.hull

    def calc_LT(self):  # expects a pandas dataframe as input
        """calculates the LT from a Hull Dataframe"""
        A_B = self.hull["Fläche"].sum()
        self.hull["L_B"] = self.hull["Fläche"] * self.hull["U-Wert"] * self.hull["Temperatur-Korrekturfaktor"]
        L_B = self.hull.L_B.sum()
        L_PX = max(0, (0.2*(0.75-L_B/A_B)*L_B)) #wärmebürkcne
        L_T = L_B + L_PX
        return L_T
        

if __name__ == "__main__":
    test = Building()
    test_ph = Building(path="../../data/building_ph.xlsx")

    bauteil = test.components[0]