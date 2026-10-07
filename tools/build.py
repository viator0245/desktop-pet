"""Build on the target OS: PyInstaller does not cross-compile Windows executables."""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--onefile',action='store_true',help='Single executable instead of a directory')
args=parser.parse_args()
command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed',
         '--onefile' if args.onefile else '--onedir','--name','SakuragiDesktopPet',
         '--add-data',f'{root / "assets"}{os.pathsep}assets',
         '--add-data',f'{root / "config.json"}{os.pathsep}.',str(root/'main.py')]
build_env = dict(os.environ)
build_env['PYINSTALLER_CONFIG_DIR'] = str(root / 'build' / '.pyinstaller-cache')
subprocess.run(command,cwd=root,check=True,env=build_env)
output=root/'dist' if args.onefile else root/'dist'/'SakuragiDesktopPet'
shutil.copy2(root/'config.json',output/'config.json')
shutil.copytree(root/'assets',output/'assets',dirs_exist_ok=True)
print(f'Built for {sys.platform}: {output}')
