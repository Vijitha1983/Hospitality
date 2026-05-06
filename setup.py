from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="hospitality",
    version="0.0.1",
    description="ERPNext Hospitality Module — Hotel, Restaurant, Bar",
    author="Vijitha Rajapaksha",
    author_email="vijitha.rajapaksha@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
