import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/jonghun/Robot_2nd_Project/install/warehouse_test_pkg'
