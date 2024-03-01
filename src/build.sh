# Dependencies: pyinstaller

# Delete current pyfish executable
rm pyfish
rm build/pyfish

pyinstaller main.py --onefile -n pyfish

# Path: src/dist/pyfish

# Delete the build folder and pyfish.spec
rm -rf build
rm pyfish.spec

# Move the pyfish executable to build folder
# create build folder if it doesn't exist
mkdir -p build
mv dist/pyfish build/pyfish

# Delete the dist folder
rm -rf dist