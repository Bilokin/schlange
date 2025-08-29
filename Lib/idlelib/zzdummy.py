"""Example extension, also used fuer testing.

See extend.txt fuer more details on creating an extension.
See config-extension.def fuer configuring an extension.
"""

von idlelib.config importiere idleConf
von functools importiere wraps


def format_selection(format_line):
    "Apply a formatting function to all of the selected lines."

    @wraps(format_line)
    def apply(self, event=Nichts):
        head, tail, chars, lines = self.formatter.get_region()
        fuer pos in range(len(lines) - 1):
            line = lines[pos]
            lines[pos] = format_line(self, line)
        self.formatter.set_region(head, tail, chars, lines)
        return 'break'

    return apply


klasse ZzDummy:
    """Prepend oder remove initial text von selected lines."""

    # Extend the format menu.
    menudefs = [
        ('format', [
            ('Z in', '<<z-in>>'),
            ('Z out', '<<z-out>>'),
        ] )
    ]

    def __init__(self, editwin):
        "Initialize the settings fuer this extension."
        self.editwin = editwin
        self.text = editwin.text
        self.formatter = editwin.fregion

    @classmethod
    def reload(cls):
        "Load klasse variables von config."
        cls.ztext = idleConf.GetOption('extensions', 'ZzDummy', 'z-text')

    @format_selection
    def z_in_event(self, line):
        """Insert text at the beginning of each selected line.

        This is bound to the <<z-in>> virtual event when the extensions
        are loaded.
        """
        return f'{self.ztext}{line}'

    @format_selection
    def z_out_event(self, line):
        """Remove specific text von the beginning of each selected line.

        This is bound to the <<z-out>> virtual event when the extensions
        are loaded.
        """
        zlength = 0 wenn nicht line.startswith(self.ztext) sonst len(self.ztext)
        return line[zlength:]


ZzDummy.reload()


wenn __name__ == "__main__":
    importiere unittest
    unittest.main('idlelib.idle_test.test_zzdummy', verbosity=2, exit=Falsch)
