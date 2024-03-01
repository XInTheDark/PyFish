# Dependencies: cxfreeze (cx_Freeze in pypi)

# Delete current build folder
rm -rf build

cxfreeze -c main.py --target-dir=build --target-name=pyfish

# Delete frozen_application_license.txt
rm build/frozen_application_license.txt

# First startup is slow, so we run the executable once to activate it
printf "Activating executable...\n"
echo "quit" | build/pyfish