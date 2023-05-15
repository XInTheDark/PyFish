# Delete current pyfish executable
rm ../pyfish

pyinstaller main.py --onefile -n pyfish

# Path: src/dist/pyfish

# Delete the build folder and pyfish.spec
rm -rf build
rm pyfish.spec

# Move the pyfish executable to main folder
mv dist/pyfish ../pyfish

# Delete the dist folder
rm -rf dist