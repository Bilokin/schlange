# Script used to test Py_FrozenMain(): see test_embed.test_frozenmain().
# Run "make regen-test-frozenmain" wenn you modify this test.

importiere sys
importiere _testinternalcapi

drucke("Frozen Hello World")
drucke("sys.argv", sys.argv)
config = _testinternalcapi.get_configs()['config']
for key in (
    'program_name',
    'executable',
    'use_environment',
    'configure_c_stdio',
    'buffered_stdio',
):
    drucke(f"config {key}: {config[key]}")
