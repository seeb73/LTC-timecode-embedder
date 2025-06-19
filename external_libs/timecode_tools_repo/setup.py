# external_libs/timecode_tools_repo/setup.py
from setuptools import setup, find_packages
import os # <--- DODAJ TĘ LINIĘ!

setup(
    name='timecode-tools-local-pkg',
    version='0.1.0',
    packages=find_packages(),
    author='Jeff Mikels (Oryginalny Autor)',
    description='Lokalna kopia narzędzi timecode, w tym ltc_encode, z repozytorium Jeffa Mikelsa.',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read() if os.path.exists(os.path.join(os.path.dirname(__file__), 'README.md')) else '',
    long_description_content_type='text/markdown',
    url='https://github.com/jeffmikels/timecode_tools',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
