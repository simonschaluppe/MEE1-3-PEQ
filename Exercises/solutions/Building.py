import pandas as pd


DEFAULT_LOADPATH = "data/building.xlsx"


class Building:
    """
    A Model of a building
    """
    def __init__(self, path=DEFAULT_LOADPATH, u_f=0.9, fensterfl_anteil=0.4):
        print("initializing Building object")
        # your code here...
        
        self.df = self.load_params(path)
        
        self.bgf = self.df.loc["gross_floor_area", "Value"] # read excel 
        self.heat_capacity = self.df.loc["effective_heat_capacity", "Value"]
        self.net_storey_height = self.df.loc["net_storey_height", "Value"]
        
        self.hull = self.load_hull(path) #from excel
        self.hull = self.insert_windows(self.hull, u_f=u_f, ff_anteil=fensterfl_anteil)
        
        self.LT = self.calc_LT(hull_df=self.hull)

    def load_params(self, path, sheetname="params"):
        """loads the sheet "params" of a excel at path and returns it as a dataframe"""
        zw = pd.read_excel(path, sheet_name=sheetname)
        zw.index = zw["Variable"]
        return zw

    def load_hull(self, path):
        """loads the sheet "thermal_ hull" of a excel at path and returns it as a dataframe"""
        hull = pd.read_excel(path, sheet_name="thermal_hull")
        return hull

    def insert_windows(self, hull_df, u_f, ff_anteil):
        """takes a hull dataframe from load_hull() and replaces an opak wall with a wall and a window entry, taking the window share and u-value as inputs"""
        aw_row = hull_df.loc[0]
        aw_A = aw_row["Fläche"]
        aw_Uwert = aw_row["U-Wert"]
        aw_tfaktor = hull_df.loc[0,"Temperatur-Korrekturfaktor"]
        
        aw_opak_A = aw_A * (1-ff_anteil)
        fenster_A = aw_A * ff_anteil 
        
        aw_opak = dict(zip(hull_df.columns,["AW (opak)", aw_opak_A, aw_Uwert, aw_tfaktor]))
        fenster = dict(zip(hull_df.columns,["Fenster", fenster_A, u_f, hull_df.loc[0,"Temperatur-Korrekturfaktor"]]))
        
        hull_df = hull_df.append(aw_opak, ignore_index = True)
        hull_df = hull_df.append(fenster, ignore_index = True)
        
        hull_df.drop(hull_df.index[0], inplace=True)
        
        return hull_df

    def calc_LT(self, hull_df):  # expects a pandas dataframe as input
        """calculates the LT from a Hull Dataframe"""
        A_B = hull_df["Fläche"].sum()
        hull_df["L_B"] = hull_df["Fläche"] * hull_df["U-Wert"] * hull_df["Temperatur-Korrekturfaktor"]
        L_B = hull_df.L_B.sum()
        L_PX = max(0, (0.2*(0.75-L_B/A_B)*L_B)) #wärmebürkcne
        L_T = L_B + L_PX
        return L_T
        

if __name__ == "__main__":
    test = Building()
    test_ph = Building(path="data/building_ph.xlsx")
    print("BGF", test.bgf)