importiere sys
von . importiere main

rc = 1
try:
    main()
    rc = 0
except Exception als e:
    drucke('Error:', e, file=sys.stderr)
sys.exit(rc)
