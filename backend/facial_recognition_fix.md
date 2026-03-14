# Step 1: Install pkg_resources explicitly
pip install pkgutil_resolve_name
pip install importlib-resources
pip install setuptools --upgrade --force-reinstall

# Step 2: Verify pkg_resources is now accessible
python -c "import pkg_resources; print('✅ pkg_resources OK')"

# Find the exact file causing the problem
cat venv/lib/python3.12/site-packages/face_recognition_models/__init__.py

# Replace the broken import with the modern equivalent
sed -i 's/from pkg_resources import resource_filename/from importlib.resources import files as _files\nfrom pathlib import Path\ndef resource_filename(package, path): return str(Path(_files(package).joinpath(path)))/' \
  venv/lib/python3.12/site-packages/face_recognition_models/__init__.py

# Verify the fix
python -c "import face_recognition_models; print('✅ models OK')"
python -c "import face_recognition; print('✅ face_recognition OK')"