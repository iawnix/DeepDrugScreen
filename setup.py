from setuptools import setup, find_packages

def read_requirements():
    with open("requirements.txt", "r") as f:
        return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

setup(
      name="DDS"
    , version="1.0"
    , author="xiaohe"
    , author_email="xiaohe@phy.ecnu.edu.cn"
    , description="A set of auxiliary programs for high-throughput screening."
    , install_requires=read_requirements()
    , packages=find_packages()
    , package_data={
          "src.config": ["*.tcss"]
    }
    , include_package_data=True         # 加入tcss文件
    , entry_points={
        "console_scripts": [
              "DBShow=src.DBShow:main"
              , "ExportDockPose=src.ExportDockPose:main"
              , "ExportDockScore=src.ExportDockScore:main"
              , "ExportSelectPose=src.ExportSelectPose:main"
              , "SbatchDock=src.SbatchDock:main"]}
    , python_requires=">=3.12"
)

