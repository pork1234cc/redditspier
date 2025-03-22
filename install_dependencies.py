import subprocess
import sys

def install_dependencies():
    """
    安装程序所需的依赖包
    """
    dependencies = [
        "praw",
        "pandas",
        "openpyxl"  # 用于Excel导出支持
    ]
    
    print("正在安装依赖...")
    
    for package in dependencies:
        print(f"安装 {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"{package} 安装成功")
        except subprocess.CalledProcessError:
            print(f"警告: {package} 安装失败")
    
    print("依赖安装完成")

if __name__ == "__main__":
    install_dependencies() 