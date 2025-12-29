from setuptools import setup

setup(
    name="hel-sync",
    version="1.0",
    description="Helwan Linux Synchronization Tool",
    author="Saeed Badrelden",
    install_requires=[
        'flask',
        'PyQt5',
        'qrcode',
        'pillow'
    ],
)