# 采用PostgreSQL作为配体数据库的后端
    - 参考: `https://zhuanlan.zhihu.com/p/514335897`
# Install
- `conda create --name dds3.5 python=3.5`
- `conda activate dds3.5`
- `conda install -c rdkit rdkit-postgresql`
# init db
- `mkdir ./MOL_LIAGND_DB`
- `initdb -D ./MOL_LIGAND_DB`
- `pg_ctl -D ./MOL_LIAGND_DB -l mol_liagnd_db.log start`
- `createdb ligand_db1`
# 构建数据库的表 
1. 所需python依赖
```python
import pandas as pd
from rdkit import Chem
from sqlalchemy import create_engine, text
from glob import glob
from tqdm import tqdm
import sascorer
```
2. 初始化一个连接
```python
engine = create_engine('postgresql://localhost/ligand_db1')
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("Info[iaw]:> Login Successfully" if result.fetchone() else "Error[iaw]:> Login Unsuccessfully")

```
3. 将数据存进数据库中，作为原始表`raw_molecules`
```python
table_name = 'raw_molecules'
all_dat.to_sql(
    table_name,
    engine,
    if_exists='replace',
    index=False,
    chunksize=100000,
    method='multi'
)
```
4. 从原始表中创建真正的分子表`molecules`
```python
with engine.connect() as conn:
    
    # 初始化molecules, 储存全局的id, iawid, smiles, 以及rdkit对象的MOL
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS molecules (
            id SERIAL PRIMARY KEY,
            iawid TEXT,
            smiles TEXT,
            m mol  -- RDKit MOL
        );
    """))
    
    # 开始填充
    conn.execute(text(f"""
        INSERT INTO molecules (iawid, smiles, m)
        SELECT
            "IAWID",
            "smile",
            mol_from_smiles("smile"::cstring)
        FROM {table_name}
        WHERE mol_from_smiles("smile"::cstring) IS NOT NULL;
    """))
    
    # 提交修改
    conn.commit()
```
5. 构建化学指纹索引用于相似性以及子结构检索
```python
def calc_chem_idx(engine):
    with engine.connect() as conn:
        print("Info[iaw]: Step 1/4, Set work mem = 4GB")
        conn.execute(text("SET maintenance_work_mem = '4GB';"))
        print("Info[iaw]:> 4GB MEM Finish.")

        # 子结构检索(GIST索引)
        print("Info[iaw]:> Step 2/4, GIST substructure index")
        conn.execute(text("CREATE INDEX mol_gist_idx ON molecules USING gist(m);"))
        conn.commit()
        print("Info[iaw]:> GIST Index Finish.")

        # morgan指纹计算
        print("Info[iaw]:> Step 3/4, Morgan Fingerprints")
        conn.execute(text("ALTER TABLE molecules ADD COLUMN fps bfp;"))
        conn.execute(text("UPDATE molecules SET fps = morganbv_fp(m, 2);"))     # 半径2
        conn.commit()
        print("Info[iaw]:> Morgan Fingerprints Finish.")
        
        # 相似性检索(GIN索引)
        print("Info[iaw]:> Step 4/4, GIN Index for similarity")
        conn.execute(text("CREATE INDEX mol_fps_idx ON molecules USING gin(fps);"))
        conn.commit()
        print("Info[iaw]:> GIN Index Finish.")

# run
calc_chem_idx(engine)

# 更新信息，并优化表
with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
    conn.execute(text("VACUUM ANALYZE molecules;"))
```
6. 分子表molecues信息

|Name|Type|Comment|
|---|---|---|
|id|main key||
|iawid||用户自定义id|
|smiles|||
|m||rdkit mol|
|fps||morgan|
|molecules_pkey|PRIMARY KEY|根据id创建的索引|
|mol_fps_idx|gin(fps)||
|mol_gist_idx|gist(m)||

7. 填充分子属性, 构建属性表
```python
def calc_base_prop(engine):
    with engine.connect() as conn:
        # MW, LogP, TPSA, HBA, HBD
        print("Info[iaw]:> Start to calc MW, LogP, TPSA, HBA and HBD.")
        conn.execute(text("""
            INSERT INTO mol_properties (mol_id, mw, logp, tpsa, hba, hbd)
            SELECT 
                id, 
                mol_amw(m),    -- MW
                mol_logp(m),   -- Wildman-Crippen LogP
                mol_tpsa(m),   -- TPSA
                mol_hba(m),    -- HBA
                mol_hbd(m)     -- HBD
            FROM molecules;
        """))
        conn.commit()
        
        # Lipinski
        print("Info[iaw]: start to calc Lipinski")
        conn.execute(text("""
            UPDATE mol_properties SET lipinski = 
                (CASE WHEN mw <= 500 THEN 1 ELSE 0 END) +
                (CASE WHEN logp <= 5 THEN 1 ELSE 0 END) +
                (CASE WHEN hba <= 10 THEN 1 ELSE 0 END) +
                (CASE WHEN hbd <= 5 THEN 1 ELSE 0 END);
        """))
        conn.commit()
        print("Info[iaw]:> Finish")

# run
calc_base_prop(engine)

def add_sa_score(engine, batch_size=50000):
    with engine.connect() as conn:
        total_rows = conn.execute(text("SELECT count(*) FROM molecules")).scalar()

        # 分批
        for offset in tqdm(range(0, total_rows, batch_size)):
            query = text(f"SELECT id, smiles FROM molecules LIMIT {batch_size} OFFSET {offset}")
            df_batch = pd.read_sql(query, conn)
            
            # calc sa
            sa_results = []
            for smis in df_batch['smiles']:
                m = Chem.MolFromSmiles(smis)
                if m:
                    score = sascorer.calculateScore(m)
                else:
                    score = None
                sa_results.append(score)

            df_batch['sa_score'] = sa_results

            # 临时表
            df_batch[['id', 'sa_score']].to_sql('temp_sa', engine, if_exists='replace', index=False)

            conn.execute(text("""
                UPDATE mol_properties p
                SET sa_score = t.sa_score
                FROM temp_sa t
                WHERE p.mol_id = t.id;
            """))
            conn.commit()

# run
add_sa_score(engine)

def calc_prop_idx(engine):
    with engine.connect() as conn:
        # MW
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prop_mw ON mol_properties(mw);"))
        # LogP
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prop_logp ON mol_properties(logp);"))
        # SA
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prop_sa ON mol_properties(sa_score);"))
        # Lipinski
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prop_lipinski ON mol_properties(lipinski);"))
        conn.commit()
calc_prop_idx(engine)

# 优化
with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
    conn.execute(text("ANALYZE mol_properties;"))
    conn.execute(text("ANALYZE molecules;"))
```



