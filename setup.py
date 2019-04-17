#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from setuptools.command.install import install
from distutils.extension import Extension
from Cython.Distutils import build_ext
import atexit
import shutil
import platform
import os
import sys


def read_version_info():
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'src/sino/scom/version.py')) as vf:
        content = vf.readlines()
        for line in content:
            if '__version__' in line:
                values = line.split('=')
                version = values[1]
                version = version.strip('\n')
                version = version.strip('\r')
                version = version.replace('\'', '')
                version = version.strip(' ')
                return version
    return '0.0.0'


sys.path.append(os.path.abspath('./src'))
__version__ = read_version_info()


class PostInstallCommand(install):
    """Post-installation step.
    """
    def run(self):
        def _post_install():
            """Post install step to copy extension modules into right location.

            Currently building extension modules with a package structure defined
            are not correctly generated by cython (0.29.7). The workaround is to
            build them in place and move them afterwards to the right location.

            Extension modules are currently generated at root level and then
            moved into sino.scom package structure. The 'move' part is done
            here in the _post_install() method.

            Keep in mind when using pip to install the sdist package that first
            a wheel package is build in the temporary folder and that the
            extension modules are build there. After finish of the
            'post install step' the files are moved from the build directory
            to the site-package directory.
            """

            def find_lib_bath(path, lib_name):
                # Check if we need to copy '.pyd' files (on Windows) or '.so' files (on Linux and macOS)
                lib_ext = '.pyd' if platform.system() in ('Windows', 'win32', 'win64') else '.so'
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.startswith(lib_name) and file.endswith(lib_ext):
                            return True, os.path.join(root, file)
                return False, ''

            def find_site_package_path(pkg_name):
                for p in sys.path:
                    pkg_path = os.path.join(p, pkg_name)
                    # Standard python installation
                    if os.path.isdir(p) and p.endswith('dist-packages') and os.path.isdir(pkg_path):
                        return p
                    # Virtual environments
                    if os.path.isdir(p) and p.endswith('site-packages') and os.path.isdir(pkg_path):
                        return p
                return None

            pkg_struct = 'sino/scom'
            site_pkg_path = find_site_package_path('setuptools')
            tmp_build_path = os.getcwd()

            # subprocess.call(['find ' + os.getcwd() + ' -iname *.so'], shell=True) # Py 3.5 and higher 'subprocess.run'

            if site_pkg_path:
                lib_move_path = os.path.join(site_pkg_path, pkg_struct)

                # Check if package structure is present in 'site-packages' folder
                if not os.path.exists(lib_move_path):
                    print('Creating package structure \'%s\'...' % pkg_struct)
                    os.makedirs(lib_move_path)

                ext_module_name = 'baseframe'
                # Searching baseframe library which was build in the build path
                success, baseframe_lib_path_and_name = find_lib_bath(tmp_build_path, ext_module_name)
                if success:
                    print('Found: %s' % baseframe_lib_path_and_name)
                    print('Copy %s to %s' % (baseframe_lib_path_and_name, lib_move_path + '/'))
                    shutil.copy(baseframe_lib_path_and_name, lib_move_path + '/')
                else:
                    print('Error: Could not find \'%s\' extension module!' % ext_module_name)

                ext_module_name = 'property'
                # Searching property library which was build in the build path
                success, property_lib_path_and_name = find_lib_bath(tmp_build_path, ext_module_name)
                if success:
                    print('Found: %s' % property_lib_path_and_name)
                    print('Copy %s to %s' % (property_lib_path_and_name, lib_move_path + '/'))
                    shutil.copy(property_lib_path_and_name, lib_move_path + '/')
                else:
                    print('Error: Could not find \'%s\' extension module!' % ext_module_name)
            else:
                print('Error: Site-package path not found!')

        atexit.register(_post_install)
        install.run(self)


setup(
    name="scom",
    version=__version__,
    description='Studer devices control library',
    url='https://www.studer-innotec.com',

    packages=find_packages('src'),
    package_dir={'': 'src'},

    ext_modules=[Extension("baseframe", ["src/sino/scom/baseframe.pyx",
                                         "src/sino/scom/scomlib/scom_data_link.c"],
                           include_dirs=['src/sino/scom'],
                           language="c++",),
                 Extension("property", ["src/sino/scom/property.pyx",
                                        "src/sino/scom/scomlib/scom_property.c"],
                           include_dirs=['src/sino/scom'],
                           language="c++",)],

    include_dirs=['src/sino/scom', ],

    cmdclass={'build_ext': build_ext,
              'install': PostInstallCommand},

    package_data={},

    data_files=[
        # First parameter is where it should be installed (relative paths or abs paths possible)
        # Second parameter is which files (from inside the project) should be taken into the dist package.
        #('sino.scom',
        # ['src/sino/scom/scomlib/scom_data_link.h',
        #  'src/sino/scom/scomlib/scom_port_c99.h',
        #  'src/sino/scom/scomlib/scom_property.h']),
    ],

    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',

        'Operating System :: OS Independent',
    ],

    maintainer='HES-SO Valais, School of Engineering, Sion',
    maintainer_email='thomas.sterren@hevs.ch',
)
