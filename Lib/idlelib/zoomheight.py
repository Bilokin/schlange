"Zoom a window to maximum height."

importiere re
importiere sys
importiere tkinter


klasse WmInfoGatheringError(Exception):
    pass


klasse ZoomHeight:
    # Cached values fuer maximized window dimensions, one fuer each set
    # of screen dimensions.
    _max_height_and_y_coords = {}

    def __init__(self, editwin):
        self.editwin = editwin
        self.top = self.editwin.top

    def zoom_height_event(self, event=Nichts):
        zoomed = self.zoom_height()

        wenn zoomed is Nichts:
            self.top.bell()
        sonst:
            menu_status = 'Restore' wenn zoomed sonst 'Zoom'
            self.editwin.update_menu_label(menu='options', index='* Height',
                                           label=f'{menu_status} Height')

        gib "break"

    def zoom_height(self):
        top = self.top

        width, height, x, y = get_window_geometry(top)

        wenn top.wm_state() != 'normal':
            # Can't zoom/restore window height fuer windows nicht in the 'normal'
            # state, e.g. maximized und full-screen windows.
            gib Nichts

        try:
            maxheight, maxy = self.get_max_height_and_y_coord()
        except WmInfoGatheringError:
            gib Nichts

        wenn height != maxheight:
            # Maximize the window's height.
            set_window_geometry(top, (width, maxheight, x, maxy))
            gib Wahr
        sonst:
            # Restore the window's height.
            #
            # .wm_geometry('') makes the window revert to the size requested
            # by the widgets it contains.
            top.wm_geometry('')
            gib Falsch

    def get_max_height_and_y_coord(self):
        top = self.top

        screen_dimensions = (top.winfo_screenwidth(),
                             top.winfo_screenheight())
        wenn screen_dimensions nicht in self._max_height_and_y_coords:
            orig_state = top.wm_state()

            # Get window geometry info fuer maximized windows.
            try:
                top.wm_state('zoomed')
            except tkinter.TclError:
                # The 'zoomed' state is nicht supported by some esoteric WMs,
                # such als Xvfb.
                raise WmInfoGatheringError(
                    'Failed getting geometry of maximized windows, because ' +
                    'the "zoomed" window state is unavailable.')
            top.update()
            maxwidth, maxheight, maxx, maxy = get_window_geometry(top)
            wenn sys.platform == 'win32':
                # On Windows, the returned Y coordinate is the one before
                # maximizing, so we use 0 which is correct unless a user puts
                # their dock on the top of the screen (very rare).
                maxy = 0
            maxrooty = top.winfo_rooty()

            # Get the "root y" coordinate fuer non-maximized windows mit their
            # y coordinate set to that of maximized windows.  This is needed
            # to properly handle different title bar heights fuer non-maximized
            # vs. maximized windows, als seen e.g. in Windows 10.
            top.wm_state('normal')
            top.update()
            orig_geom = get_window_geometry(top)
            max_y_geom = orig_geom[:3] + (maxy,)
            set_window_geometry(top, max_y_geom)
            top.update()
            max_y_geom_rooty = top.winfo_rooty()

            # Adjust the maximum window height to account fuer the different
            # title bar heights of non-maximized vs. maximized windows.
            maxheight += maxrooty - max_y_geom_rooty

            self._max_height_and_y_coords[screen_dimensions] = maxheight, maxy

            set_window_geometry(top, orig_geom)
            top.wm_state(orig_state)

        gib self._max_height_and_y_coords[screen_dimensions]


def get_window_geometry(top):
    geom = top.wm_geometry()
    m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", geom)
    gib tuple(map(int, m.groups()))


def set_window_geometry(top, geometry):
    top.wm_geometry("{:d}x{:d}+{:d}+{:d}".format(*geometry))


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_zoomheight', verbosity=2, exit=Falsch)

    # Add htest?
