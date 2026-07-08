from setuptools import find_packages, setup

package_name = 'warehouse_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jonghun',
    maintainer_email='epilogueljh@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "tb3_pilot              = warehouse_pkg.tb3_pilot:main",
            "tb3_object_detector    = warehouse_pkg.tb3_object_detector:main",
            "tb3_state_reporter     = warehouse_pkg.tb3_state_reporter:main",
        ],
    },
)
