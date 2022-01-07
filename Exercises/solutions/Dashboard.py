import bokeh.plotting
import panel as pn
from Simulation import Model


class Dashboard:
    # build the dashboard
    def __init__(self, model: Model = None):
        self.model = model

        self.header = pn.Row(
            pn.pane.Markdown(f"""
                # MEE1-3 PEQ Dashboard
                """)
        )
        bgf = model.building.bgf
        self.in_pv_kWp = pn.widgets.FloatSlider(start=0, end=round(bgf/10), value=model.PV.kWp,
                                                name="PV Size (kWp)",
                                                )
        self.in_battery_kWh = pn.widgets.FloatSlider(start=0, end=round(bgf/10), value=model.battery.capacity,
            name="Battery Size (kWh)",
            # placeholder="kWh"
        )

        self.run_button = pn.widgets.Button(name="Simulate", button_type="primary")
        self.run_button.on_click(self.run)

        self.model_repr = pn.pane.Markdown(self.model.__repr__().replace("\n", "\n\n"))

        self.inputs = pn.Column(
            pn.pane.Markdown("""
                ## Inputs
                """),
            self.in_pv_kWp,
            self.in_battery_kWh,
            self.run_button,
            self.model_repr

        )

        self.elplot = pn.pane.Bokeh(self.el_plot())
        self.heatplot = pn.pane.Bokeh(self.heat_balance_plot())

        self.layout = pn.Column(
            self.header,
            pn.Row(
                self.inputs, self.elplot, self.heatplot
            )
        )

    def run(self, event):
        self.update_inputs()
        self.model.simulate()
        print(self.model)
        self.update_outputs()

    # update the dashboard
    def update_inputs(self):
        self.model.PV.set_kWp(float(self.in_pv_kWp.value))
        self.model.battery.capacity = float(self.in_battery_kWh.value)

    def update_outputs(self):
        self.model_repr.object = self.model.__repr__().replace("\n", "\n\n")
        self.elplot.object = self.el_plot()
        self.heatplot.object = self.heat_balance_plot()

    def el_plot(self) -> bokeh.plotting.figure:
        """returns a bokeh figure for the heat balance of the model"""
        if not self.model.simulated:
            raise ValueError("not simulated yet!")

        df = self.model.df_electricity_use
        p = bokeh.plotting.figure(
            title="Electricity Use",
            x_axis_label="",
            y_axis_label="Energy Flow [W/m²BGFa]",
            tools="hover, pan, reset,save,box_zoom",
            x_axis_type="datetime",
            plot_height=400,
            tooltips="@index: @value"
            # x_range=[1, 8760]
        )
        colors = {
             "PV Eigenverbrauch": "yellow",
            'Batterie-Entladung': "lime",
            "Netzstrom": "grey",
            "Batterie-Beladung": "purple",
            "Einspeisung": "orange"}

        for col in df:  # col is a string
            p.step(x="index", y=col, source=df, legend_label=col, line_width=1, color=colors[col])
        return p

    def heat_balance_plot(self) -> bokeh.plotting.figure:
        """returns a bokeh figure for the heat balance of the model"""
        if not self.model.simulated:
            raise ValueError("not simulated yet!")

        df = self.model.df_heat_balance
        p = bokeh.plotting.figure(
            title="Heat Balance",
            x_axis_label="",
            y_axis_label="Energy Flow [W/m²BGFa]",
            tools="hover, pan, reset,save,box_zoom",
            x_axis_type="datetime",
            plot_height=400,
            tooltips="@index: @value"
            # x_range=[1, 8760]
        )
        colors = {
            "Transmissionsverluste": "#ff4400",
            "Lüftungsverluste": "#0055FF",
            "Solare Gewinne": "#ffee00",
            "Innere Lasten": "#FF0000",
            "Heizwärmebedarf": "#ff4400",
            "Kühlbedarf": "#00DDFF",
        }

        for col in df:  # col is a string
            p.step(x="index", y=col, source=df, legend_label=col, line_width=1, color=colors[col])
        return p


if __name__ == "__main__":
    model = Model()
    model.simulate()
    d = Dashboard(model=model)
    d.layout.show()
