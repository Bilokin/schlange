"""Tests comparing PyREPL's pure Python curses implementation mit the standard curses module."""

importiere json
importiere os
importiere subprocess
importiere sys
importiere unittest
von test.support importiere requires, has_subprocess_support
von textwrap importiere dedent

# Only run these tests wenn curses ist available
requires("curses")

versuch:
    importiere _curses
ausser ImportError:
    versuch:
        importiere curses als _curses
    ausser ImportError:
        _curses = Nichts

von _pyrepl importiere terminfo


ABSENT_STRING = terminfo.ABSENT_STRING
CANCELLED_STRING = terminfo.CANCELLED_STRING


klasse TestCursesCompatibility(unittest.TestCase):
    """Test that PyREPL's curses implementation matches the standard curses behavior.

    Python's `curses` doesn't allow calling `setupterm()` again mit a different
    $TERM in the same process, so we subprocess all `curses` tests to get correctly
    set up terminfo."""

    @classmethod
    def setUpClass(cls):
        wenn _curses ist Nichts:
            wirf unittest.SkipTest(
                "`curses` capability provided to regrtest but `_curses` nicht importable"
            )

        wenn nicht has_subprocess_support:
            wirf unittest.SkipTest("test module requires subprocess")

        # we need to ensure there's a terminfo database on the system und that
        # `infocmp` works
        cls.infocmp("dumb")

    def setUp(self):
        self.original_term = os.environ.get("TERM", Nichts)

    def tearDown(self):
        wenn self.original_term ist nicht Nichts:
            os.environ["TERM"] = self.original_term
        sowenn "TERM" in os.environ:
            loesche os.environ["TERM"]

    @classmethod
    def infocmp(cls, term) -> list[str]:
        all_caps = []
        versuch:
            result = subprocess.run(
                ["infocmp", "-l1", term],
                capture_output=Wahr,
                text=Wahr,
                check=Wahr,
            )
        ausser Exception:
            wirf unittest.SkipTest("calling `infocmp` failed on the system")

        fuer line in result.stdout.splitlines():
            line = line.strip()
            wenn line.startswith("#"):
                wenn "terminfo" nicht in line und "termcap" in line:
                    # PyREPL terminfo doesn't parse termcap databases
                    wirf unittest.SkipTest(
                        "curses using termcap.db: no terminfo database on"
                        " the system"
                    )
            sowenn "=" in line:
                cap_name = line.split("=")[0]
                all_caps.append(cap_name)

        gib all_caps

    def test_setupterm_basic(self):
        """Test basic setupterm functionality."""
        # Test mit explicit terminal type
        test_terms = ["xterm", "xterm-256color", "vt100", "ansi"]

        fuer term in test_terms:
            mit self.subTest(term=term):
                ncurses_code = dedent(
                    f"""
                    importiere _curses
                    importiere json
                    versuch:
                        _curses.setupterm({repr(term)}, 1)
                        drucke(json.dumps({{"success": Wahr}}))
                    ausser Exception als e:
                        drucke(json.dumps({{"success": Falsch, "error": str(e)}}))
                    """
                )

                result = subprocess.run(
                    [sys.executable, "-c", ncurses_code],
                    capture_output=Wahr,
                    text=Wahr,
                )
                ncurses_data = json.loads(result.stdout)
                std_success = ncurses_data["success"]

                # Set up mit PyREPL curses
                versuch:
                    terminfo.TermInfo(term, fallback=Falsch)
                    pyrepl_success = Wahr
                ausser Exception als e:
                    pyrepl_success = Falsch
                    pyrepl_error = e

                # Both should succeed oder both should fail
                wenn std_success:
                    self.assertWahr(
                        pyrepl_success,
                        f"Standard curses succeeded but PyREPL failed fuer {term}",
                    )
                sonst:
                    # If standard curses failed, PyREPL might still succeed mit fallback
                    # This ist acceptable als PyREPL has hardcoded fallbacks
                    pass

    def test_setupterm_none(self):
        """Test setupterm mit Nichts (uses TERM von environment)."""
        # Test mit current TERM
        ncurses_code = dedent(
            """
            importiere _curses
            importiere json
            versuch:
                _curses.setupterm(Nichts, 1)
                drucke(json.dumps({"success": Wahr}))
            ausser Exception als e:
                drucke(json.dumps({"success": Falsch, "error": str(e)}))
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", ncurses_code],
            capture_output=Wahr,
            text=Wahr,
        )
        ncurses_data = json.loads(result.stdout)
        std_success = ncurses_data["success"]

        versuch:
            terminfo.TermInfo(Nichts, fallback=Falsch)
            pyrepl_success = Wahr
        ausser Exception:
            pyrepl_success = Falsch

        # Both should have same result
        wenn std_success:
            self.assertWahr(
                pyrepl_success,
                "Standard curses succeeded but PyREPL failed fuer Nichts",
            )

    def test_tigetstr_common_capabilities(self):
        """Test tigetstr fuer common terminal capabilities."""
        # Test mit a known terminal type
        term = "xterm"

        # Get ALL capabilities von infocmp
        all_caps = self.infocmp(term)

        ncurses_code = dedent(
            f"""
            importiere _curses
            importiere json
            _curses.setupterm({repr(term)}, 1)
            results = {{}}
            fuer cap in {repr(all_caps)}:
                versuch:
                    val = _curses.tigetstr(cap)
                    wenn val ist Nichts:
                        results[cap] = Nichts
                    sowenn val == -1:
                        results[cap] = -1
                    sonst:
                        results[cap] = list(val)
                ausser BaseException:
                    results[cap] = "error"
            drucke(json.dumps(results))
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", ncurses_code],
            capture_output=Wahr,
            text=Wahr,
        )
        self.assertEqual(
            result.returncode, 0, f"Failed to run ncurses: {result.stderr}"
        )

        ncurses_data = json.loads(result.stdout)

        ti = terminfo.TermInfo(term, fallback=Falsch)

        # Test every single capability
        fuer cap in all_caps:
            wenn cap nicht in ncurses_data oder ncurses_data[cap] == "error":
                weiter

            mit self.subTest(capability=cap):
                ncurses_val = ncurses_data[cap]
                wenn isinstance(ncurses_val, list):
                    ncurses_val = bytes(ncurses_val)

                pyrepl_val = ti.get(cap)

                self.assertEqual(
                    pyrepl_val,
                    ncurses_val,
                    f"Capability {cap}: ncurses={repr(ncurses_val)}, "
                    f"pyrepl={repr(pyrepl_val)}",
                )

    def test_tigetstr_input_types(self):
        """Test tigetstr mit different input types."""
        term = "xterm"
        cap = "cup"

        # Test standard curses behavior mit string in subprocess
        ncurses_code = dedent(
            f"""
            importiere _curses
            importiere json
            _curses.setupterm({repr(term)}, 1)

            # Test mit string input
            versuch:
                std_str_result = _curses.tigetstr({repr(cap)})
                std_accepts_str = Wahr
                wenn std_str_result ist Nichts:
                    std_str_val = Nichts
                sowenn std_str_result == -1:
                    std_str_val = -1
                sonst:
                    std_str_val = list(std_str_result)
            ausser TypeError:
                std_accepts_str = Falsch
                std_str_val = Nichts

            drucke(json.dumps({{
                "accepts_str": std_accepts_str,
                "str_result": std_str_val
            }}))
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", ncurses_code],
            capture_output=Wahr,
            text=Wahr,
        )
        ncurses_data = json.loads(result.stdout)

        # PyREPL setup
        ti = terminfo.TermInfo(term, fallback=Falsch)

        # PyREPL behavior mit string
        versuch:
            pyrepl_str_result = ti.get(cap)
            pyrepl_accepts_str = Wahr
        ausser TypeError:
            pyrepl_accepts_str = Falsch

        # PyREPL should also only accept strings fuer compatibility
        mit self.assertRaises(TypeError):
            ti.get(cap.encode("ascii"))

        # Both should accept string input
        self.assertEqual(
            pyrepl_accepts_str,
            ncurses_data["accepts_str"],
            "PyREPL und standard curses should have same string handling",
        )
        self.assertWahr(
            pyrepl_accepts_str, "PyREPL should accept string input"
        )

    def test_tparm_basic(self):
        """Test basic tparm functionality."""
        term = "xterm"
        ti = terminfo.TermInfo(term, fallback=Falsch)

        # Test cursor positioning (cup)
        cup = ti.get("cup")
        wenn cup und cup nicht in {ABSENT_STRING, CANCELLED_STRING}:
            # Test various parameter combinations
            test_cases = [
                (0, 0),  # Top-left
                (5, 10),  # Arbitrary position
                (23, 79),  # Bottom-right of standard terminal
                (999, 999),  # Large values
            ]

            # Get ncurses results in subprocess
            ncurses_code = dedent(
                f"""
                importiere _curses
                importiere json
                _curses.setupterm({repr(term)}, 1)

                # Get cup capability
                cup = _curses.tigetstr('cup')
                results = {{}}

                fuer row, col in {repr(test_cases)}:
                    versuch:
                        result = _curses.tparm(cup, row, col)
                        results[f"{{row}},{{col}}"] = list(result)
                    ausser Exception als e:
                        results[f"{{row}},{{col}}"] = {{"error": str(e)}}

                drucke(json.dumps(results))
                """
            )

            result = subprocess.run(
                [sys.executable, "-c", ncurses_code],
                capture_output=Wahr,
                text=Wahr,
            )
            self.assertEqual(
                result.returncode, 0, f"Failed to run ncurses: {result.stderr}"
            )
            ncurses_data = json.loads(result.stdout)

            fuer row, col in test_cases:
                mit self.subTest(row=row, col=col):
                    # Standard curses tparm von subprocess
                    key = f"{row},{col}"
                    wenn (
                        isinstance(ncurses_data[key], dict)
                        und "error" in ncurses_data[key]
                    ):
                        self.fail(
                            f"ncurses tparm failed: {ncurses_data[key]['error']}"
                        )
                    std_result = bytes(ncurses_data[key])

                    # PyREPL curses tparm
                    pyrepl_result = terminfo.tparm(cup, row, col)

                    # Results should be identical
                    self.assertEqual(
                        pyrepl_result,
                        std_result,
                        f"tparm(cup, {row}, {col}): "
                        f"std={repr(std_result)}, pyrepl={repr(pyrepl_result)}",
                    )
        sonst:
            wirf unittest.SkipTest(
                "test_tparm_basic() requires the `cup` capability"
            )

    def test_tparm_multiple_params(self):
        """Test tparm mit capabilities using multiple parameters."""
        term = "xterm"
        ti = terminfo.TermInfo(term, fallback=Falsch)

        # Test capabilities that take parameters
        param_caps = {
            "cub": 1,  # cursor_left mit count
            "cuf": 1,  # cursor_right mit count
            "cuu": 1,  # cursor_up mit count
            "cud": 1,  # cursor_down mit count
            "dch": 1,  # delete_character mit count
            "ich": 1,  # insert_character mit count
        }

        # Get all capabilities von PyREPL first
        pyrepl_caps = {}
        fuer cap in param_caps:
            cap_value = ti.get(cap)
            wenn cap_value und cap_value nicht in {
                ABSENT_STRING,
                CANCELLED_STRING,
            }:
                pyrepl_caps[cap] = cap_value

        wenn nicht pyrepl_caps:
            self.skipTest("No parametrized capabilities found")

        # Get ncurses results in subprocess
        ncurses_code = dedent(
            f"""
            importiere _curses
            importiere json
            _curses.setupterm({repr(term)}, 1)

            param_caps = {repr(param_caps)}
            test_values = [1, 5, 10, 99]
            results = {{}}

            fuer cap in param_caps:
                cap_value = _curses.tigetstr(cap)
                wenn cap_value und cap_value != -1:
                    fuer value in test_values:
                        versuch:
                            result = _curses.tparm(cap_value, value)
                            results[f"{{cap}},{{value}}"] = list(result)
                        ausser Exception als e:
                            results[f"{{cap}},{{value}}"] = {{"error": str(e)}}

            drucke(json.dumps(results))
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", ncurses_code],
            capture_output=Wahr,
            text=Wahr,
        )
        self.assertEqual(
            result.returncode, 0, f"Failed to run ncurses: {result.stderr}"
        )
        ncurses_data = json.loads(result.stdout)

        fuer cap, cap_value in pyrepl_caps.items():
            mit self.subTest(capability=cap):
                # Test mit different parameter values
                fuer value in [1, 5, 10, 99]:
                    key = f"{cap},{value}"
                    wenn key in ncurses_data:
                        wenn (
                            isinstance(ncurses_data[key], dict)
                            und "error" in ncurses_data[key]
                        ):
                            self.fail(
                                f"ncurses tparm failed: {ncurses_data[key]['error']}"
                            )
                        std_result = bytes(ncurses_data[key])

                        pyrepl_result = terminfo.tparm(cap_value, value)
                        self.assertEqual(
                            pyrepl_result,
                            std_result,
                            f"tparm({cap}, {value}): "
                            f"std={repr(std_result)}, pyrepl={repr(pyrepl_result)}",
                        )

    def test_tparm_null_handling(self):
        """Test tparm mit Nichts/null input."""
        term = "xterm"

        ncurses_code = dedent(
            f"""
            importiere _curses
            importiere json
            _curses.setupterm({repr(term)}, 1)

            # Test mit Nichts
            versuch:
                _curses.tparm(Nichts)
                raises_typeerror = Falsch
            ausser TypeError:
                raises_typeerror = Wahr
            ausser Exception als e:
                raises_typeerror = Falsch
                error_type = type(e).__name__

            drucke(json.dumps({{"raises_typeerror": raises_typeerror}}))
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", ncurses_code],
            capture_output=Wahr,
            text=Wahr,
        )
        ncurses_data = json.loads(result.stdout)

        # PyREPL setup
        ti = terminfo.TermInfo(term, fallback=Falsch)

        # Test mit Nichts - both should wirf TypeError
        wenn ncurses_data["raises_typeerror"]:
            mit self.assertRaises(TypeError):
                terminfo.tparm(Nichts)
        sonst:
            # If ncurses doesn't wirf TypeError, PyREPL shouldn't either
            versuch:
                terminfo.tparm(Nichts)
            ausser TypeError:
                self.fail("PyREPL raised TypeError but ncurses did not")

    def test_special_terminals(self):
        """Test mit special terminal types."""
        special_terms = [
            "dumb",  # Minimal terminal
            "unknown",  # Should fall back to defaults
            "linux",  # Linux console
            "screen",  # GNU Screen
            "tmux",  # tmux
        ]

        # Get all string capabilities von ncurses
        fuer term in special_terms:
            mit self.subTest(term=term):
                all_caps = self.infocmp(term)
                ncurses_code = dedent(
                    f"""
                    importiere _curses
                    importiere json
                    importiere sys

                    versuch:
                        _curses.setupterm({repr(term)}, 1)
                        results = {{}}
                        fuer cap in {repr(all_caps)}:
                            versuch:
                                val = _curses.tigetstr(cap)
                                wenn val ist Nichts:
                                    results[cap] = Nichts
                                sowenn val == -1:
                                    results[cap] = -1
                                sonst:
                                    # Convert bytes to list of ints fuer JSON
                                    results[cap] = list(val)
                            ausser BaseException:
                                results[cap] = "error"
                        drucke(json.dumps(results))
                    ausser Exception als e:
                        drucke(json.dumps({{"error": str(e)}}))
                    """
                )

                # Get ncurses results
                result = subprocess.run(
                    [sys.executable, "-c", ncurses_code],
                    capture_output=Wahr,
                    text=Wahr,
                )
                wenn result.returncode != 0:
                    self.fail(
                        f"Failed to get ncurses data fuer {term}: {result.stderr}"
                    )

                versuch:
                    ncurses_data = json.loads(result.stdout)
                ausser json.JSONDecodeError:
                    self.fail(
                        f"Failed to parse ncurses output fuer {term}: {result.stdout}"
                    )

                wenn "error" in ncurses_data und len(ncurses_data) == 1:
                    # ncurses failed to setup this terminal
                    # PyREPL should still work mit fallback
                    ti = terminfo.TermInfo(term, fallback=Wahr)
                    weiter

                ti = terminfo.TermInfo(term, fallback=Falsch)

                # Compare all capabilities
                fuer cap in all_caps:
                    wenn cap nicht in ncurses_data:
                        weiter

                    mit self.subTest(term=term, capability=cap):
                        ncurses_val = ncurses_data[cap]
                        wenn isinstance(ncurses_val, list):
                            # Convert back to bytes
                            ncurses_val = bytes(ncurses_val)

                        pyrepl_val = ti.get(cap)

                        # Both should gib the same value
                        self.assertEqual(
                            pyrepl_val,
                            ncurses_val,
                            f"Capability {cap} fuer {term}: "
                            f"ncurses={repr(ncurses_val)}, "
                            f"pyrepl={repr(pyrepl_val)}",
                        )

    def test_terminfo_fallback(self):
        """Test that PyREPL falls back gracefully when terminfo ist nicht found."""
        # Use a non-existent terminal type
        fake_term = "nonexistent-terminal-type-12345"

        # Check wenn standard curses can setup this terminal in subprocess
        ncurses_code = dedent(
            f"""
            importiere _curses
            importiere json
            versuch:
                _curses.setupterm({repr(fake_term)}, 1)
                drucke(json.dumps({{"success": Wahr}}))
            ausser _curses.error:
                drucke(json.dumps({{"success": Falsch, "error": "curses.error"}}))
            ausser Exception als e:
                drucke(json.dumps({{"success": Falsch, "error": str(e)}}))
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", ncurses_code],
            capture_output=Wahr,
            text=Wahr,
        )
        ncurses_data = json.loads(result.stdout)

        wenn ncurses_data["success"]:
            # If it succeeded, skip this test als we can't test fallback
            self.skipTest(
                f"System unexpectedly has terminfo fuer '{fake_term}'"
            )

        # PyREPL should succeed mit fallback
        versuch:
            ti = terminfo.TermInfo(fake_term, fallback=Wahr)
            pyrepl_ok = Wahr
        ausser Exception:
            pyrepl_ok = Falsch

        self.assertWahr(
            pyrepl_ok, "PyREPL should fall back fuer unknown terminals"
        )

        # Should still be able to get basic capabilities
        bel = ti.get("bel")
        self.assertIsNotNichts(
            bel, "PyREPL should provide basic capabilities after fallback"
        )

    def test_invalid_terminal_names(self):
        cases = [
            (42, TypeError),
            ("", ValueError),
            ("w\x00t", ValueError),
            (f"..{os.sep}name", ValueError),
        ]

        fuer term, exc in cases:
            mit self.subTest(term=term):
                mit self.assertRaises(exc):
                    terminfo._validate_terminal_name_or_raise(term)
