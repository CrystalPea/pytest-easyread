from setuptools import setup

setup(
    name='pytest-easyread',
    description='py.test plugin that makes terminal printouts of the reports easier to read',
    long_description=open("README.md").read(),
    version='0.0.0',
    url='https://github.com/CrystalPea/pytest-easyread',
    license='BSD',
    author='Pea Tyczynska',
    py_modules=['pytest_easyread'],
    entry_points={'pytest11': ['easyread = pytest_easyread']},
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=['pytest>=2.9'],
    classifiers=[
        "Framework :: Pytest"
    ]
)
