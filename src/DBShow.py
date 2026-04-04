import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from textual import work, on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Sparkline, Digits, Input, DataTable, ContentSwitcher, Button, RadioSet, RadioButton
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.binding import Binding

src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))

from config.constants import MOVIE_3, INFO_SIDEBAR
from util.rdkit_postgresql.DB_Module import ligand_db_manager

import os
from dotenv import load_dotenv
load_dotenv()
PSQ_DB_HOST = os.getenv("PSQ_DB_HOST")
PSQ_DB_PORT = os.getenv("PSQ_DB_PORT")
PSQ_DB_USR = os.getenv("PSQ_DB_USR")
PSQ_DB_PASSWD = os.getenv("PSQ_DB_PASSWD")
PSQ_DB_NAME = os.getenv("PSQ_DB_NAME")


CSS_FILE_PATH = src_path / "config" / "db_tui_style.tcss"

class SidebarBackground(Static):
    # Author Info
    def on_mount(self) -> None:
        self.update(INFO_SIDEBAR)

class RunningAnimation(Static):
    # ASCII Moive
    def on_mount(self) -> None:
        self.frames = MOVIE_3
        self.current_frame = 0
        self.set_interval(0.22, self.next_frame)

    def next_frame(self) -> None:
        art = self.frames[self.current_frame].replace(r"\n", "\n")
        self.update("[cyan]{}[/]\n[italic][#64D2FF]Calculating...[/]".format(art))
        self.current_frame = (self.current_frame + 1) % len(self.frames)

class PropertyChart(Static):
    # Mol Prop Info
    def __init__(self, title: str, prop_name: str):
        super().__init__()
        self.title = title
        self.prop_name = prop_name

    def compose(self) -> ComposeResult:
        yield Label("󱎏 {}".format(self.title), classes="chart-title-text")
        yield RunningAnimation(id="loading-{}".format(self.prop_name), classes="loader")
        yield Sparkline(id="spark-{}".format(self.prop_name), classes="hidden")

class StatCard(Static):
    
    # Sum of mol in database 
    def __init__(self, label: str, id: str):
        super().__init__(id=id)
        self.label = label

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.label, classes="card-label")
            yield Digits("0", id="{}-digits".format(self.id))


class DB_TUI(App):

    # key map
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True), 
        Binding("f5", "refresh_db", "Refresh", show=True),
        Binding("f1", "show_status", "Status", show=True),
        Binding("f2", "show_search", "Search", show=True),
        Binding("f3", "show_export", "Export", show=True)
    ]
    
    CSS_PATH = CSS_FILE_PATH

    def compose(self) -> ComposeResult:
        yield Footer()
        with Grid(id="main-grid"):

            # time
            with Horizontal(id="clock-container"):
                yield Digits("", id="clock-digits")
            
            # sum of mol and author info
            with Vertical(classes="stat-sidebar"):
                with Vertical(id="sidebar-top"):
                    yield StatCard("Total Molecules", id="total-count")
                yield Static("", id="sidebar-divider")
                with Vertical(id="sidebar-bottom"):
                    yield SidebarBackground()
            
            # status bar
            yield Static("DBShow: Initializing...", id="status-bar")
            
            # main interactive area
            with ContentSwitcher(initial="charts-view", id="main-switcher", classes="right-content-area"):
                
                # Function 1 <f1>: Show mol prop info 
                with Container(id="charts-view", classes="charts-container"):
                    yield PropertyChart("Molecular Weight", "mw")
                    yield PropertyChart("LogP", "logp")
                    yield PropertyChart("TPSA", "tpsa")
                    yield PropertyChart("SA Score", "sa_score")
                
                # Function 2 <2>: Search mol
                with Container(id="search-view"):
                    yield Label("󱘶 Molecule Search", classes="search-title")
                    with Horizontal(classes="search-inputs"):
                        yield Input(placeholder="Input SMILES", id="input-smiles", classes="search-input")
                        yield Input(placeholder="Input IAWID", id="input-iawid", classes="search-input")
                        yield Button("Search", id="btn-search", variant="primary")
                    yield RunningAnimation(id="search-anim", classes="hidden")
                    yield DataTable(id="search-results")
                
                # Function 3 <f3>: Batch filter & export
                with Container(id="export-view"):
                    yield Label(" Batch Filter & Export to CSV", classes="search-title")
                    
                    with Horizontal(classes="export-mode-selector"):
                        yield Label("Select Mode: ")
                        with RadioSet(id="export-mode-radios"):
                            yield RadioButton("Similarity", id="radio-sim", value=True)
                            yield RadioButton("Substructure", id="radio-sub")
                            yield RadioButton("Properties", id="radio-prop")

                    with Vertical(id="export-params-container"):
                        yield Input(placeholder="Target SMILES", id="export-smiles", classes="export-input")
                        yield Input(placeholder="Similarity Threshold (e.g. 0.7)", value="0.7", id="export-thresh", classes="export-input")
                        yield Input(placeholder="Max Results Limit (e.g. 10000)", value="10000", id="export-limit", classes="export-input")
                        
                        with Vertical(id="export-prop-inputs", classes="hidden"):
                            yield Input(placeholder="MW range (e.g. 200,500)", id="prop-mw", classes="export-input")
                            yield Input(placeholder="LogP range (e.g. 0,5)", id="prop-logp", classes="export-input")
                            yield Input(placeholder="TPSA range (e.g. 20,100)", id="prop-tpsa", classes="export-input")

                    with Horizontal(classes="export-actions"):
                        yield Input(placeholder="Output Filename (e.g. output.csv)", value="output.csv", id="export-filename", classes="export-input")
                        yield Button("Run & Export", id="btn-export", variant="success")
                    
                    yield Label("", id="export-status-label")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_clock)
        self.load_database_data()

    # function for key bindings
    def action_show_status(self) -> None:
        switcher = self.query_one("#main-switcher", ContentSwitcher)
        switcher.current = "charts-view"
        self.query_one("#status-bar").update("Info[iaw]:> Overview Mode: Active. Press F2 to Search, F3 to Export.")
        self.set_focus(None)

    def action_show_search(self) -> None:
        switcher = self.query_one("#main-switcher", ContentSwitcher)
        switcher.current = "search-view"
        self.query_one("#status-bar").update("Info[iaw]:> Search Mode: Active. Input SMILES/IAWID and press Enter.")
        self.query_one("#input-smiles").focus()
        
    def action_show_export(self) -> None:
        switcher = self.query_one("#main-switcher", ContentSwitcher)
        switcher.current = "export-view"
        self.query_one("#status-bar").update("Info[iaw]:> Export Mode: Active. Press Enter to run export.")
        self.query_one("#export-smiles").focus()

    def action_refresh_db(self) -> None:
        switcher = self.query_one("#main-switcher", ContentSwitcher)
        if switcher.current == "charts-view":
            self.query_one("#status-bar").update("Info[iaw]:> Refreshing database...")
            self.load_database_data()
        else:
            self.notify("Error[iaw]:> Refresh (F5) is only available in Stats Mode (F1).", severity="error")


    # Enter Key
    @on(Input.Submitted)
    def handle_inputs_submit(self, event: Input.Submitted) -> None:

        # <F2>
        if event.input.id in ["input-smiles", "input-iawid"]:
            self.handle_search_action()
        # <F3>
        elif event.input.id in ["export-smiles", "export-thresh", "export-limit", "prop-mw", "prop-logp", "prop-tpsa", "export-filename"]:
            self.execute_export()

    # Export Mode
    @on(RadioSet.Changed, "#export-mode-radios")
    def handle_export_mode_change(self, event: RadioSet.Changed) -> None:
        selected_id = event.pressed.id
        
        smiles_input = self.query_one("#export-smiles")
        thresh_input = self.query_one("#export-thresh")
        limit_input = self.query_one("#export-limit")
        prop_inputs = self.query_one("#export-prop-inputs")
        
        match selected_id:
            case "radio-sim":
                smiles_input.display = True
                thresh_input.display = True
                limit_input.display = True
                prop_inputs.display = False
            case "radio-sub":
                smiles_input.display = True
                thresh_input.display = False
                limit_input.display = True
                prop_inputs.display = False
            case "radio-prop":
                smiles_input.display = False
                thresh_input.display = False
                limit_input.display = False
                prop_inputs.display = True
            # 这种情况应该不存在
            case _:
                smiles_input.display = False
                thresh_input.display = False
                limit_input.display = False
                prop_inputs.display = False


    @on(Button.Pressed, "#btn-export")
    def handle_export_button(self, event: Button.Pressed) -> None:
        self.execute_export()

    def execute_export(self) -> None:

        radios = self.query_one("#export-mode-radios", RadioSet)
        if not radios.pressed_button:
            return None
            
        mode_id = radios.pressed_button.id
        filename = self.query_one("#export-filename").value.strip() or "output.csv"
        params = {}

        if mode_id in ["radio-sim", "radio-sub"]:
            params["smiles"] = self.query_one("#export-smiles").value.strip()
            params["limit"] = int(self.query_one("#export-limit").value.strip() or 10000)
            if mode_id == "radio-sim":
                params["thresh"] = float(self.query_one("#export-thresh").value.strip() or 0.7)
                
            if not params["smiles"]:
                self.notify("Error[iaw]:> Target SMILES is required for this mode!", severity="error")
                return None

        elif mode_id == "radio-prop":
            conditions = {}
            for prop in ["mw", "logp", "tpsa"]:
                val = self.query_one(f"#prop-{prop}").value.strip()
                if val:
                    try:
                        vmin, vmax = map(float, val.split(","))
                        conditions[prop] = (vmin, vmax)
                    except ValueError:
                        self.notify("Error[iaw]:> Invalid format for {}. Use 'min,max' (e.g. 200,500)".format(prop.upper()), severity="error")
                        return
            if not conditions:
                self.notify("Error[iaw]:> At least one property condition is required!", severity="error")
                return
            params["conditions"] = conditions

        self.run_export_task(mode_id, params, filename)

    @work(exclusive=True)
    async def run_export_task(self, mode_id: str, params: dict, filename: str) -> None:
        status_label = self.query_one("#export-status-label")
        status_label.update("󰔟 Querying database and generating CSV, please wait...")
        self.query_one("#btn-export").disabled = True

        try:
            if mode_id == "radio-sim":
                df = await asyncio.to_thread(
                    self.db.search_by_similarity, params["smiles"], params["thresh"], include_props=True, limit=params["limit"]
                )
            elif mode_id == "radio-sub":
                df = await asyncio.to_thread(
                    self.db.search_by_substructure, params["smiles"], include_props=True, limit=params["limit"]
                )
            elif mode_id == "radio-prop":
                df = await asyncio.to_thread(
                    self.db.filter_by_prop, params["conditions"]
                )

            if df is not None and not df.empty:
                await asyncio.to_thread(df.to_csv, filename, index=False)
                status_label.update("Info[iaw]:> Success! Exported {} molecules to `{}`.".format(len(df), filename))
            else:
                status_label.update("Warning[iaw]:>: No molecules matched the given criteria.")
                
        except Exception as e:
            self.notify("Error[iaw]:> Export Failed: {}".format(e), severity="error")
            status_label.update("Error[iaw]:> Export Failed: {}".format(e))
        finally:
            self.query_one("#btn-export").disabled = False


    # --- 检索视图交互逻辑 ---
    @on(Button.Pressed, "#btn-search")
    def on_search_button_pressed(self, event: Button.Pressed) -> None:
        self.handle_search_action()
        
    def handle_search_action(self) -> None:
        smiles_val = self.query_one("#input-smiles").value.strip()
        iawid_val = self.query_one("#input-iawid").value.strip()

        if smiles_val:
            self.query_one("#input-iawid").value = ""
            self.run_search_task("smiles", smiles_val)
        elif iawid_val:
            self.run_search_task("iawid", iawid_val)
        else:
            self.notify("Please enter either a SMILES or an IAWID.", severity="error")

    @work(exclusive=True)
    async def run_search_task(self, search_type: str, query: str) -> None:
        table = self.query_one("#search-results", DataTable)
        anim = self.query_one("#search-anim")
        
        table.add_class("hidden")
        anim.remove_class("hidden")
        self.query_one("#status-bar").update("󰔟 Searching by {}...".format(search_type))
        
        try:
            if search_type == "smiles":
                df = await asyncio.to_thread(self.db.search_by_smiles, query)
            else:
                df = await asyncio.to_thread(self.db.search_by_iawid, query)
            
            self._update_table(df)
            self.query_one("#status-bar").update("Info[iaw]:> Search Completed. Found {} results.".format(len(df) if df is not None else 0))
        except Exception as e:
            self.notify("Error[iaw]:> Search Failed: {}".format(e), severity="error")
            self.query_one("#status-bar").update("Error[iaw]:> Search Failed.")
        finally:
            anim.add_class("hidden")
            table.remove_class("hidden")

    def _update_table(self, df) -> None:
        table = self.query_one("#search-results", DataTable)
        table.clear(columns=True)
        
        if df is not None and not df.empty:
            df = df.fillna("")
            columns = [str(col).upper() for col in df.columns.tolist()]
            table.add_columns(*columns)
            for _, row in df.iterrows():
                table.add_row(*[str(val) for val in row.tolist()])
        else:
            table.add_columns("Result")
            table.add_row("No molecules found.")


    # --- 底层环境维持逻辑 ---
    def update_clock(self) -> None:
        self.query_one("#clock-digits").update(datetime.now().strftime("%H:%M:%S"))

    async def load_single_property(self, prop_name: str) -> None:
        try:
            dist = await asyncio.to_thread(self.db.get_property_distribution, prop_name, bins=40)
            if dist and dist.get("values"):
                valid_values = [v for v in dist["values"] if v is not None]
                if valid_values:
                    self.query_one(f"#loading-{prop_name}").display = False
                    spark = self.query_one(f"#spark-{prop_name}")
                    spark.remove_class("hidden")
                    spark.data = valid_values
        except Exception:
            self.query_one(f"#loading-{prop_name}").update(f"[red]Error[/]")

    @work(exclusive=True)
    async def load_database_data(self) -> None:
        try:
            db_url = f"postgresql://{PSQ_DB_USR}:{PSQ_DB_PASSWD}@{PSQ_DB_HOST}:{PSQ_DB_PORT}/{PSQ_DB_NAME}"
            self.db = ligand_db_manager(db_url)
            await asyncio.to_thread(self.db.connect)
            if not self.db.is_connected:
                return

            await asyncio.gather(
                asyncio.to_thread(self.update_total_count),
                self.load_single_property("mw"),
                self.load_single_property("logp"),
                self.load_single_property("tpsa"),
                self.load_single_property("sa_score")
            )
            self.query_one("#status-bar").update("Info[iaw]:> Data Synchronized. F1: Stats, F2: Search, F3: Export.")
        except Exception as e:
            self.notify("Error[iaw]:> Connection Failed: {}".format(e), severity="error")

    def update_total_count(self) -> None:
        count = self.db.get_total_count()
        self.query_one("#total-count-digits").update(f"{count}")
        
if __name__ == "__main__":
    DB_TUI().run()
