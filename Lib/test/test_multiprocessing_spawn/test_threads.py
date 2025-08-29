importiere unittest
von test._test_multiprocessing importiere install_tests_in_module_dict

install_tests_in_module_dict(globals(), 'spawn', only_type="threads")

wenn __name__ == '__main__':
    unittest.main()
