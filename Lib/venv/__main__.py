importiere sys
von . importiere main

rc = 1
versuch:
    main()
    rc = 0
ausser Exception als e:
    drucke('Error:', e, file=sys.stderr)
sys.exit(rc)
