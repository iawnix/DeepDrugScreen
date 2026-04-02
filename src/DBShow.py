import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from textual import work, on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Sparkline, Digits, Input, DataTable, ContentSwitcher, Button
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.binding import Binding

# 路径配置
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
    """侧边栏底部的项目信息与字符画装饰组件"""
    def on_mount(self) -> None:
        self.update(INFO_SIDEBAR)

class RunningAnimation(Static):
    """机器人跳舞 ASCII 动态加载动画"""
    def on_mount(self) -> None:
        self.frames = MOVIE_3
        self.current_frame = 0
        self.set_interval(0.22, self.next_frame)

    def next_frame(self) -> None:
        art = self.frames[self.current_frame].replace(r"\n", "\n")
        self.update(f"[cyan]{art}[/]\n[italic][#64D2FF]Calculating...[/]")
        self.current_frame = (self.current_frame + 1) % len(self.frames)

class PropertyChart(Static):
    """分子属性图表组件"""
    def __init__(self, title: str, prop_name: str):
        super().__init__()
        self.title = title
        self.prop_name = prop_name

    def compose(self) -> ComposeResult:
        yield Label(f"📊 {self.title}", classes="chart-title-text")
        yield RunningAnimation(id=f"loading-{self.prop_name}", classes="loader")
        yield Sparkline(id=f"spark-{self.prop_name}", classes="hidden")

class StatCard(Static):
    """侧边栏统计卡片"""
    def __init__(self, label: str, id: str):
        super().__init__(id=id)
        self.label = label

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.label, classes="card-label")
            yield Digits("0", id=f"{self.id}-digits")


class LigandTUI(App):
    # 【核心修改区】使用 F1, F2, F5 彻底避开终端拦截以及 SMILES 字符输入冲突
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True), 
        Binding("f5", "refresh_db", "Refresh", show=True),
        Binding("f1", "show_stats", "Stats (Charts)", show=True),
        Binding("f2", "show_search", "Search", show=True)
    ]
    
    CSS_PATH = CSS_FILE_PATH

    def compose(self) -> ComposeResult:
        yield Footer()

        with Grid(id="main-grid"):
            # 顶部：时钟
            with Horizontal(id="clock-container"):
                yield Digits("", id="clock-digits")
            
            # 左侧：侧边栏
            with Vertical(classes="stat-sidebar"):
                with Vertical(id="sidebar-top"):
                    yield StatCard("Total Molecules", id="total-count")
                yield Static("", id="sidebar-divider")
                with Vertical(id="sidebar-bottom"):
                    yield SidebarBackground()
            
            # 中间：状态栏
            yield Static("🚀 RDKit Engine: Initializing...", id="status-bar")
            
            # 右侧主要区域：使用 ContentSwitcher 实现视图切换
            with ContentSwitcher(initial="charts-view", id="main-switcher", classes="right-content-area"):
                
                # 视图 1 (默认): 属性分布图表 (由 F1 触发)
                with Container(id="charts-view", classes="charts-container"):
                    yield PropertyChart("Molecular Weight", "mw")
                    yield PropertyChart("LogP", "logp")
                    yield PropertyChart("TPSA", "tpsa")
                    yield PropertyChart("SA Score", "sa_score")
                
                # 视图 2: 分子检索界面 (由 F2 触发)
                with Container(id="search-view"):
                    yield Label("🔍 Molecule Search Engine", classes="search-title")
                    with Horizontal(classes="search-inputs"):
                        yield Input(placeholder="Input SMILES", id="input-smiles", classes="search-input")
                        yield Input(placeholder="Input IAWID", id="input-iawid", classes="search-input")
                        yield Button("Search", id="btn-search", variant="primary")
                    yield RunningAnimation(id="search-anim", classes="hidden")
                    yield DataTable(id="search-results")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_clock)
        self.load_database_data()

    def action_show_stats(self) -> None:
        """按下 F1: 切换到属性分布图表界面"""
        switcher = self.query_one("#main-switcher", ContentSwitcher)
        switcher.current = "charts-view"
        self.query_one("#status-bar").update("✅ Chart Mode: Active. Press F2 to search.")
        self.set_focus(None) # 清除输入框焦点

    def action_show_search(self) -> None:
        """按下 F2: 切换到搜索界面"""
        switcher = self.query_one("#main-switcher", ContentSwitcher)
        switcher.current = "search-view"
        self.query_one("#status-bar").update("🔍 Search Mode: Active. Input SMILES/IAWID and click Search.")
        self.query_one("#input-smiles").focus()

    def action_refresh_db(self) -> None:
        """按下 F5: 严格按照要求，只有在图表模式(F1)下才执行刷新"""
        switcher = self.query_one("#main-switcher", ContentSwitcher)
        if switcher.current == "charts-view":
            self.query_one("#status-bar").update("🔄 Refreshing database...")
            self.load_database_data()
        else:
            # 如果在检索界面(F2)按 F5，给予警告并拒绝刷新
            self.notify("Refresh (F5) is only available in Stats Mode (F1).", severity="warning")

    @on(Button.Pressed, "#btn-search")
    def handle_search_button(self, event: Button.Pressed) -> None:
        """点击 Search 按钮触发的事件"""
        smiles_val = self.query_one("#input-smiles").value.strip()
        iawid_val = self.query_one("#input-iawid").value.strip()

        if smiles_val:
            self.query_one("#input-iawid").value = "" # 自动清空另一侧
            self.run_search_task("smiles", smiles_val)
        elif iawid_val:
            self.run_search_task("iawid", iawid_val)
        else:
            self.notify("Please enter either a SMILES or an IAWID.", severity="error")

    @work(exclusive=True)
    async def run_search_task(self, search_type: str, query: str) -> None:
        """异步执行数据库检索"""
        table = self.query_one("#search-results", DataTable)
        anim = self.query_one("#search-anim")
        
        table.add_class("hidden")
        anim.remove_class("hidden")
        self.query_one("#status-bar").update(f"⏳ Searching by {search_type}...")
        
        try:
            if search_type == "smiles":
                df = await asyncio.to_thread(self.db.search_by_smiles, query)
            else:
                df = await asyncio.to_thread(self.db.search_by_iawid, query)
            
            self._update_table(df)
            self.query_one("#status-bar").update(f"✅ Search Completed. Found {len(df) if df is not None else 0} results.")
        except Exception as e:
            self.notify(f"Search Failed: {e}", severity="error")
            self.query_one("#status-bar").update("❌ Search Failed.")
        finally:
            anim.add_class("hidden")
            table.remove_class("hidden")

    def _update_table(self, df) -> None:
        """将 Pandas DataFrame 渲染到 Textual DataTable 组件中"""
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
            self.query_one("#status-bar").update("✅ Data Synchronized. Press F2 to search.")
        except Exception as e:
            self.notify(f"Connection Failed: {e}", severity="error")

    def update_total_count(self) -> None:
        count = self.db.get_total_count()
        self.query_one("#total-count-digits").update(f"{count}")
        
if __name__ == "__main__":
    LigandTUI().run()