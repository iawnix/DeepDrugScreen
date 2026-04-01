from textual.app import App, ComposeResult
from textual.widgets import Button, Digits, Footer, Header


class DeepDrugScreen(App):
    
    BINDINGS = [("d", "mol_dock", "Dock"), 
                ("s", "mol_show", "show ligand infos in database")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_mol_dock() -> None:
        pass

    def action_mol_show() -> None:
        pass
    

if __name__ == "__main__":
    app = DeepDrugScreen()
    app.run()






