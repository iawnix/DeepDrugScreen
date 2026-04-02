import pandas as pd
from rdkit import Chem
from sqlalchemy import create_engine, text, Engine, Connection

from typing import Optional, List, Dict, Any, Union, Tuple

from glob import glob
from tqdm import tqdm

class ligand_db_manager:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url
        self.engine = create_engine(self.db_url, pool_pre_ping=True)
        self._is_connected = False

    def connect(self) -> None:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._is_connected = True
            print("Info[iaw]:> Successfully connected to the database.")
        except Exception as e:
            self._is_connected = False
            print("Error[iaw]:> Failed to connect to the database: {}".format(e=str(e)))

    def disconnect(self) -> None:
        if self._is_connected:
            self.engine.dispose()
            self._is_connected = False
            print("Info[iaw]:> Disconnected from the database.")
        else:
            print("Warning[iaw]:> No active database connection to disconnect.")
    @property
    def is_connected(self) -> bool:
        """返回当前数据库连接状态。"""
        return self._is_connected

    def search_by_smiles(self, smiles: str) -> pd.DataFrame:
        """通过 SMILES 精确查询分子及其理化性质。"""
        query = text("""
            SELECT m.iawid, m.smiles, p.mw, p.logp, p.tpsa, p.hba, p.hbd, p.lipinski, p.sa_score FROM molecules m 
            JOIN mol_properties p ON m.id = p.mol_id 
            WHERE m.m = mol_from_smiles(CAST(:s AS cstring));
        """)
        with self.engine.connect() as conn:
            return pd.read_sql(query, conn, params={"s": smiles})
    
    def search_by_iawid(self, iawid: str) -> pd.DataFrame:
        """通过 IAWID 查询分子结构及性质。"""
        query = text("""
            SELECT m.iawid, m.smiles, p.mw, p.logp, p.tpsa, p.hba, p.hbd, p.lipinski, p.sa_score FROM molecules m 
            JOIN mol_properties p ON m.id = p.mol_id 
            WHERE m.iawid = :id;
        """)
        with self.engine.connect() as conn:
            return pd.read_sql(query, conn, params={"id": iawid})
    
    def filter_by_prop(self, conditions: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
        """
        基于理化性质范围筛选。
        :param conditions: 字典格式 {'mw': (200, 500), 'logp': (0, 5)}
        """
        base_query = "SELECT m.iawid, m.smiles FROM molecules m JOIN mol_properties p ON m.id = p.mol_id WHERE 1=1"
        params = {}
        for idx, (col, (vmin, vmax)) in enumerate(conditions.items()):
            base_query += f" AND p.{col} BETWEEN :min_{idx} AND :max_{idx}"
            params[f"min_{idx}"] = vmin
            params[f"max_{idx}"] = vmax
        
        with self.engine.connect() as conn:
            return pd.read_sql(text(base_query), conn, params=params)
    
    def _search_engine(self, smiles: str, mode: str = "substruct", 
                       threshold: float = 0.7, limit: int = 100, 
                       include_props: bool = False) -> pd.DataFrame:
        """
        内部搜索引擎。mode: 'substruct' (骨架) 或 'similarity' (相似性)
        """
        select_clause = "m.iawid, m.smiles" + (", p.*" if include_props else "")
        join_clause = "JOIN mol_properties p ON m.id = p.mol_id" if include_props else ""
        
        if mode == "substruct":
            where_clause = "m.m @> mol_from_smiles(CAST(:s AS cstring))"
        else:
            where_clause = "m.fps % morganbv_fp(mol_from_smiles(CAST(:s AS cstring)), 2)"

        query = text(f"SELECT {select_clause} FROM molecules m {join_clause} WHERE {where_clause} LIMIT :l")
        
        with self.engine.connect() as conn:
            if mode == "similarity":
                conn.execute(text(f"SET rdkit.tanimoto_threshold = {threshold}"))
            return pd.read_sql(query, conn, params={"s": smiles, "l": limit})

    # include_props为True会返回属性列，False则只返回iawid和smiles
    def search_by_similarity(self, smiles: str, threshold: float = 0.7, include_props: bool = False, limit: int = 10000) -> pd.DataFrame:
        """相似性搜索 API。"""
        return self._search_engine(smiles, "similarity", threshold, include_props=include_props, limit = limit)
    
    # include_props为True会返回属性列，False则只返回iawid和smiles
    def search_by_substructure(self, smiles: str, include_props: bool = False, limit: int = 10000) -> pd.DataFrame:
        """子结构/骨架搜索 API。"""
        return self._search_engine(smiles, "substruct", include_props=include_props, limit = limit)

    def get_total_count(self) -> int:
        """获取数据库中分子总数。"""
        with self.engine.connect() as conn:
            return conn.execute(text("SELECT count(*) FROM molecules")).scalar()

    def get_property_distribution(self, column: str, bins: int = 10) -> Dict[str, Any]:
        """
        获取理化性质的分布情况（用于 TUI 绘图）。
        返回: {'bin_edges': [], 'counts': []}
        """
        # SQL 原生计算直方图，避免将千万数据拉取到内存
        query = text(f"""
            SELECT width_bucket({column}, min_val, max_val, :b) as bucket,
                   count(*) as cnt,
                   min({column}) as range_start
            FROM mol_properties, 
                 (SELECT min({column}) as min_val, max({column}) as max_val FROM mol_properties) as stats
            GROUP BY bucket ORDER BY bucket;
        """)
        with self.engine.connect() as conn:
            result = conn.execute(query, {"b": bins}).fetchall()
            return {
                "labels": [f"{float(r[2]):.2f}" for r in result],
                "values": [r[1] for r in result]
            }