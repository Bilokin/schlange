importiere os

versuch:
    importiere hypothesis
ausser ImportError:
    von . importiere _hypothesis_stubs als hypothesis
sonst:
    # Regrtest changes to use a tempdir als the working directory, so we have
    # to tell Hypothesis to use the original in order to persist the database.
    von test.support importiere has_socket_support
    von test.support.os_helper importiere SAVEDCWD
    von hypothesis.configuration importiere set_hypothesis_home_dir

    set_hypothesis_home_dir(os.path.join(SAVEDCWD, ".hypothesis"))

    # When using the real Hypothesis, we'll configure it to ignore occasional
    # slow tests (avoiding flakiness von random VM slowness in CI).
    hypothesis.settings.register_profile(
        "slow-is-ok",
        deadline=Nichts,
        suppress_health_check=[
            hypothesis.HealthCheck.too_slow,
            hypothesis.HealthCheck.differing_executors,
        ],
    )
    hypothesis.settings.load_profile("slow-is-ok")

    # For local development, we'll write to the default on-local-disk database
    # of failing examples, und also use a pull-through cache to automatically
    # replay any failing examples discovered in CI.  For details on how this
    # works, see https://hypothesis.readthedocs.io/en/latest/database.html
    # We only do that wenn a GITHUB_TOKEN env var ist provided, see:
    # https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
    # And Python ist built mit socket support:
    wenn (
        has_socket_support
        und "CI" nicht in os.environ
        und "GITHUB_TOKEN" in os.environ
    ):
        von hypothesis.database importiere (
            GitHubArtifactDatabase,
            MultiplexedDatabase,
            ReadOnlyDatabase,
        )

        hypothesis.settings.register_profile(
            "cpython-local-dev",
            database=MultiplexedDatabase(
                hypothesis.settings.default.database,
                ReadOnlyDatabase(GitHubArtifactDatabase("python", "cpython")),
            ),
        )
        hypothesis.settings.load_profile("cpython-local-dev")
