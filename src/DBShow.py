import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Sparkline, Digits
from textual.containers import Container, Vertical, Horizontal, Grid
from textual import work

# 路径配置
src_path = Path(__file__).parent.resolve()
sys.path.append(str(src_path))

from config.constants import PSQ_DB_HOST, PSQ_DB_PORT, PSQ_DB_USR, PSQ_DB_PASSWD, PSQ_DB_NAME, MOVIE_3, INFO_SIDEBAR
from util.rdkit_postgresql.DB_Module import ligand_db_manager

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

    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]
    CSS_PATH = CSS_FILE_PATH

    def compose(self) -> ComposeResult:

        with Grid(id="main-grid"):
            # 顶部：时钟
            with Horizontal(id="clock-container"):
                yield Digits("", id="clock-digits")
            
            # 左侧：侧边栏
            with Vertical(classes="stat-sidebar"):
                # 上部分：统计
                with Vertical(id="sidebar-top"):
                    yield StatCard("Total Molecules", id="total-count")
                
                # 分割线
                yield Static("", id="sidebar-divider")
                
                # 下部分：项目详情
                with Vertical(id="sidebar-bottom"):
                    yield SidebarBackground()
            
            # 中间：状态栏
            yield Static("🚀 RDKit Engine: Initializing...", id="status-bar")
            
            # 右侧主要区域：分布图表
            with Container(classes="charts-container"):
                yield PropertyChart("Molecular Weight", "mw")
                yield PropertyChart("LogP", "logp")
                yield PropertyChart("TPSA", "tpsa")
                yield PropertyChart("SA Score", "sa_score")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_clock)
        self.load_database_data()

    def action_refresh(self) -> None:
        self.load_database_data()

    def update_clock(self) -> None:
        self.query_one("#clock-digits").update(datetime.now().strftime("%H:%M:%S"))

    async def load_single_property(self, prop_name: str) -> None:
        """独立加载单个属性并处理异常"""
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
        """并发启动子任务"""
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
            self.query_one("#status-bar").update("✅ Data Synchronized")
        except Exception as e:
            self.notify(f"Connection Failed: {e}", severity="error")

    def update_total_count(self) -> None:
        count = self.db.get_total_count()
        self.query_one("#total-count-digits").update(f"{count}")
        
if __name__ == "__main__":
    LigandTUI().run()