#!/bin/bash
pushd .
cd $(dirname $0)/../..

name=nnc_uploader_$(uname -s | tr '[A-Z]' '[a-z]')_$(uname -m)

virtualenv __build_uploader
. __build_uploader/bin/activate

pip install tqdm requests boto3 pyinstaller

rm -rf dist/$name/*
pyinstaller --specpath $(pwd)/build/mac --clean --workpath $(pwd)/build/work --distpath $(pwd)/dist/$name --icon=$(pwd)/img/uploader.icns --onefile --windowed src/gui.py 
pyinstaller --specpath $(pwd)/build/mac --clean --workpath $(pwd)/build/work --distpath $(pwd)/dist/$name --onefile src/uploader.py

tar cjf dist/${name}_tools.tar.bz2 dist/$name
cd dist
mkdir gui
zip -r gui/$name.zip $name/gui.app
cd ..

deactivate

popd
