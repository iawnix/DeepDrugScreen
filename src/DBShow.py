import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Sparkline, LoadingIndicator, Digits
from textual.containers import Container, Vertical, Horizontal, Grid
from textual import work

# 1. 环境与配置加载
# 获取 src 目录的路径
src_path = Path(__file__).parent.resolve()
project_root = src_path.parent
sys.path.append(str(src_path))

from config.constants import PSQ_DB_HOST, PSQ_DB_PORT, PSQ_DB_USR, PSQ_DB_PASSWD, PSQ_DB_NAME
from util.rdkit_postgresql.DB_Module import ligand_db_manager

# 修正后的 CSS 路径定位
CSS_FILE_PATH = src_path / "config" / "db_tui_style.tcss"

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

    # 使用从文件加载的 CSS
    CSS_PATH = CSS_FILE_PATH

    def compose(self) -> ComposeResult:
        yield Header()
        
        # 0. 启动遮罩层 (Layer: overlay)
        with Container(id="loading-overlay"):
            yield LoadingIndicator()
            yield Label("SYSTEM INITIALIZING: Loading Database Distribution...")

        # 1. 主界面 (Layer: base)
        with Grid(id="main-grid"):
            # 顶部时钟
            with Horizontal(id="clock-container"):
                yield Digits("", id="clock-digits")

            # 左侧统计栏
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
        # 显示遮罩
        self.query_one("#loading-overlay").display = True
        # 启动时钟定时器
        self.set_interval(1.0, self.update_clock)
        # 异步加载数据
        self.load_database_data()

    def update_clock(self) -> None:
        """更新数码管时间样式"""
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
            self.db = ligand_db_manager(db_url)
            self.db.connect()

            # 1. 更新分子总数
            count = self.db.get_total_count()
            self.query_one("#total-count-digits").update(f"{count}")

            # 2. 获取属性分布并填充 Sparkline
            props = ["mw", "logp", "tpsa", "sa_score"]
            for p in props:
                dist = self.db.get_property_distribution(p, bins=40)
                self.query_one(f"#spark-{p}").data = dist["values"]

            # 3. 处理 Avg MW 和 Valid SA (由于 DB_Module 缺少对应方法，这里演示如何从分布数据计算或设为 N/A)
            # 这里暂时更新为从分布中获取的近似值或保持占位
            # 真实开发中建议您在 DB_Module 添加对应聚合函数
            self.query_one("#avg-mw-digits").update("SCAN")
            self.query_one("#valid-sa-digits").update("DATA")

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