import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Sparkline, LoadingIndicator, Digits
from textual.containers import Container, Vertical, Horizontal, Grid
from textual import work

# 1. 环境与配置加载
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
from config.constants import PSQ_DB_HOST, PSQ_DB_PORT, PSQ_DB_USR, PSQ_DB_PASSWD, PSQ_DB_NAME

CSS_FILE_PATH = project_root/ "src" / "config" / "db_tui_style.tcss"

# 2. 自定义组件定义
class StatCard(Static):
    """侧边栏统计卡片"""
    def __init__(self, label: str, value: str = "0", id: str = None):
        super().__init__(id=id)
        self.label = label
        self.value = value

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.label, classes="card-title")
            yield Digits(self.value, id=f"{self.id}-digits")

class PropertyChart(Static):
    """右侧属性分布图卡片"""
    def __init__(self, title: str, prop_name: str):
        super().__init__()
        self.title = title
        self.prop_name = prop_name

    def compose(self) -> ComposeResult:
        yield Label(f"📊 {self.title} Distribution")
        yield Sparkline(id=f"spark-{self.prop_name}")

# 3. 主程序类
class LigandTUI(App):
    TITLE = "LigandDB Explorer v2.0"
    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh Data")]

    CSS_PATH = CSS_FILE_PATH

    def compose(self) -> ComposeResult:
        yield Header()
        
        # 0. 启动遮罩层 (Layer: overlay)
        with Container(id="loading-overlay"):
            yield LoadingIndicator()
            yield Label("SYSTEM INITIALIZING: Connecting to Postgres...")

        # 1. 主界面 (Layer: base)
        with Grid(id="main-grid"):
            # 顶部时钟
            with Horizontal(id="clock-container"):
                yield Digits("", id="clock-digits")

            # 左侧统计
            with Vertical(classes="stat-sidebar"):
                yield StatCard("Total Molecules", id="total-count")
                yield StatCard("Avg MW", id="avg-mw")
                yield StatCard("Valid SA", id="valid-sa")
            
            # 状态提示
            yield Static("🚀 RDKit Cartridge Engine | Connected to ligand_db1", classes="stat-card")

            # 右侧图表区
            with Container(classes="charts-container"):
                yield PropertyChart("Molecular Weight", "mw")
                yield PropertyChart("LogP", "logp")
                yield PropertyChart("TPSA", "tpsa")
                yield PropertyChart("SA Score", "sa_score")
        
        yield Footer()

    def on_mount(self) -> None:
        """界面挂载后立即执行"""
        # 显示遮罩并启动任务
        self.query_one("#loading-overlay").display = True
        self.set_interval(1.0, self.update_clock)
        self.load_database_data()

    def update_clock(self) -> None:
        """更新数码管时间"""
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d  %H:%M:%S")
        self.query_one("#clock-digits").update(time_str)

    @work(exclusive=True)
    async def load_database_data(self) -> None:
        """核心数据加载逻辑"""
        overlay = self.query_one("#loading-overlay")
        overlay.display = True 
        
        try:
            # 建立数据库连接
            db_url = f"postgresql://{PSQ_DB_USR}:{PSQ_DB_PASSWD}@{PSQ_DB_HOST}:{PSQ_DB_PORT}/{PSQ_DB_NAME}"
            from util.rdkit_postgresql.DB_Module import ligand_db_manager
            self.db = ligand_db_manager(db_url)
            self.db.connect()

            # 1. 获取基础统计
            count = self.db.get_total_count()
            self.query_one("#total-count-digits").update(f"{count}")

            # 2. 获取高级统计数据 (Avg MW, Valid SA)
            stats = self.db.get_stats() 
            self.query_one("#avg-mw-digits").update(f"{stats['avg_mw']}")
            self.query_one("#valid-sa-digits").update(f"{stats['valid_sa']}")

            # 3. 异步并行更新四个图表
            props = ["mw", "logp", "tpsa", "sa_score"]
            for p in props:
                dist = self.db.get_property_distribution(p, bins=40)
                self.query_one(f"#spark-{p}").data = dist["values"]

        except Exception as e:
            self.notify(f"DATABASE ERROR: {e}", severity="error", timeout=10)
        finally:
            # 加载完成，撤除遮罩
            overlay.display = False

    def action_refresh(self):
        """按下 'R' 键刷新数据"""
        self.load_database_data()

if __name__ == "__main__":
    LigandTUI().run()