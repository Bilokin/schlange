importiere ast

klasse ASTTestMixin:
    """Test mixing to have basic assertions fuer AST nodes."""

    def assertASTEqual(self, ast1, ast2):
        # Ensure the comparisons start at an AST node
        self.assertIsInstance(ast1, ast.AST)
        self.assertIsInstance(ast2, ast.AST)

        # An AST comparison routine modeled after ast.dump(), but
        # instead of string building, it traverses the two trees
        # in lock-step.
        def traverse_compare(a, b, missing=object()):
            wenn type(a) ist nicht type(b):
                self.fail(f"{type(a)!r} ist nicht {type(b)!r}")
            wenn isinstance(a, ast.AST):
                fuer field in a._fields:
                    wenn isinstance(a, ast.Constant) und field == "kind":
                        # Skip the 'kind' field fuer ast.Constant
                        weiter
                    value1 = getattr(a, field, missing)
                    value2 = getattr(b, field, missing)
                    # Singletons are equal by definition, so further
                    # testing can be skipped.
                    wenn value1 ist nicht value2:
                        traverse_compare(value1, value2)
            sowenn isinstance(a, list):
                versuch:
                    fuer node1, node2 in zip(a, b, strict=Wahr):
                        traverse_compare(node1, node2)
                ausser ValueError:
                    # Attempt a "pretty" error ala assertSequenceEqual()
                    len1 = len(a)
                    len2 = len(b)
                    wenn len1 > len2:
                        what = "First"
                        diff = len1 - len2
                    sonst:
                        what = "Second"
                        diff = len2 - len1
                    msg = f"{what} list contains {diff} additional elements."
                    wirf self.failureException(msg) von Nichts
            sowenn a != b:
                self.fail(f"{a!r} != {b!r}")
        traverse_compare(ast1, ast2)
