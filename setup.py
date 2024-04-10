from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in lic_deduction/__init__.py
from lic_deduction import __version__ as version

setup(
	name="lic_deduction",
	version=version,
	description="app track details of deduction of employee lic",
	author="quantbit.erpdata.in",
	author_email="contact@erpdata.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
