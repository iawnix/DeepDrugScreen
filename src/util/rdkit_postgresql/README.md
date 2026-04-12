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


