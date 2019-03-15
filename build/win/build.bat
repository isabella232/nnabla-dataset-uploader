echo off
pushd .
cd %~dp0..\..

REM set http_proxy=http://proxy.kanto.sony.co.jp:10080/
REM conda create -n uploader python=3.7
REM conda activate uploader
REM pip install pyinstaller boto3 requests tqdm

SET nnabla_iwr_options=-Proxy "http://proxy.kanto.sony.co.jp:10080"
SET http_proxy=proxy.kanto.sony.co.jp:10080
SET https_proxy=proxy.kanto.sony.co.jp:10080

SET CONDA_ENV_PATH=c:\tools\Miniconda3\envs
SET CONDA_ENV=uploader

SET PATH_PYTHON=%CONDA_ENV_PATH%\%CONDA_ENV%
SET PATH_PYTHON=%CONDA_ENV_PATH%\%CONDA_ENV%\Library\mingw-w64\bin;%PATH_PYTHON%
SET PATH_PYTHON=%CONDA_ENV_PATH%\%CONDA_ENV%\Library\usr\bin;%PATH_PYTHON%
SET PATH_PYTHON=%CONDA_ENV_PATH%\%CONDA_ENV%\Library\bin;%PATH_PYTHON%
SET PATH_PYTHON=%CONDA_ENV_PATH%\%CONDA_ENV%\Scripts;%PATH_PYTHON%

SET PATH=%PATH_PYTHON%;%PATH%

pyinstaller --clean --specpath build/win --workpath build/work --distpath dist/nnc_uploader_win64 --icon=img/uploader.ico --add-data ..\..\img\uploader.ico;img --onefile --windowed src/gui.py 
pyinstaller --clean --specpath build/win --workpath build/work --distpath dist/nnc_uploader_win64 --onefile src/uploader.py

zip -r9 dist/nnc_uploader_win64_tools.zip dist/nnc_uploader_win64

cd dist
mkdir gui
zip -r9 gui/nnc_uploader_win64.zip nnc_uploader_win64/gui.exe
cd ..

popd
