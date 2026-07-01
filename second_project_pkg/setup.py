from setuptools import find_packages, setup

package_name = 'second_project_pkg'

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
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        	"navigation_coltroller  = second_project_pkg.navigation_coltroller:main",
            "navigation_test        = second_project_pkg.navigation_test:main",
            "navigation_test_lidar  = second_project_pkg.navigation_test_lidar:main",
            "object_detector        = second_project_pkg.object_detector:main",
            "object_detector_gazebo = second_project_pkg.object_detector_gazebo:main",
        ],
    },
)
