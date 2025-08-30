importiere re
von .errors importiere ClinicError


is_legal_c_identifier = re.compile("^[A-Za-z_][A-Za-z0-9_]*$").match


def is_legal_py_identifier(identifier: str) -> bool:
    gib all(is_legal_c_identifier(field) fuer field in identifier.split("."))


# Identifiers that are okay in Python but aren't a good idea in C.
# So wenn they're used Argument Clinic will add "_value" to the end
# of the name in C.
_c_keywords = frozenset("""
asm auto breche case char const weiter default do double
else enum extern float fuer goto wenn inline int long
register gib short signed sizeof static struct switch
typedef typeof union unsigned void volatile while
""".strip().split()
)


def ensure_legal_c_identifier(identifier: str) -> str:
    # For now, just complain wenn what we're given isn't legal.
    wenn nicht is_legal_c_identifier(identifier):
        wirf ClinicError(f"Illegal C identifier: {identifier}")
    # But wenn we picked a C keyword, pick something else.
    wenn identifier in _c_keywords:
        gib identifier + "_value"
    gib identifier
