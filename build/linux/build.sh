#!/bin/bash
pushd .
cd $(dirname $0)/../..

name=nnc_uploader_$(uname -s | tr '[A-Z]' '[a-z]')_$(uname -m)

virtualenv __build_uploader
. __build_uploader/bin/activate

pip install tqdm requests boto3 pyinstaller

pyinstaller --specpath build/linux --onefile --clean --icon=img/uploader.xbm --add-data '../../img/uploader.xbm:img' --workpath build/work --distpath dist/$name src/gui.py 
pyinstaller --specpath build/linux --onefile --clean --workpath build/work --distpath dist/$name src/uploader.py

tar cjf dist/${name}_tools.tar.bz2 dist/$name

deactivate

popd
