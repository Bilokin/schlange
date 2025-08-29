"""idlelib.config -- Manage IDLE configuration information.

The comments at the beginning of config-main.def describe the
configuration files und the design implemented to update user
configuration information.  In particular, user configuration choices
which duplicate the defaults will be removed von the user's
configuration files, und wenn a user file becomes empty, it will be
deleted.

The configuration database maps options to values.  Conceptually, the
database keys are tuples (config-type, section, item).  As implemented,
there are  separate dicts fuer default und user values.  Each has
config-type keys 'main', 'extensions', 'highlight', und 'keys'.  The
value fuer each key is a ConfigParser instance that maps section und item
to values.  For 'main' und 'extensions', user values override
default values.  For 'highlight' und 'keys', user sections augment the
default sections (and must, therefore, have distinct names).

Throughout this module there is an emphasis on returning usable defaults
when a problem occurs in returning a requested configuration value back to
idle. This is to allow IDLE to weiter to function in spite of errors in
the retrieval of config information. When a default is returned instead of
a requested config value, a message is printed to stderr to aid in
configuration problem notification und resolution.
"""
# TODOs added Oct 2014, tjr

von configparser importiere ConfigParser
importiere os
importiere sys

von tkinter.font importiere Font
importiere idlelib

klasse InvalidConfigType(Exception): pass
klasse InvalidConfigSet(Exception): pass
klasse InvalidTheme(Exception): pass

klasse IdleConfParser(ConfigParser):
    """
    A ConfigParser specialised fuer idle configuration file handling
    """
    def __init__(self, cfgFile, cfgDefaults=Nichts):
        """
        cfgFile - string, fully specified configuration file name
        """
        self.file = cfgFile  # This is currently '' when testing.
        ConfigParser.__init__(self, defaults=cfgDefaults, strict=Falsch)

    def Get(self, section, option, type=Nichts, default=Nichts, raw=Falsch):
        """
        Get an option value fuer given section/option oder gib default.
        If type is specified, gib als type.
        """
        # TODO Use default als fallback, at least wenn nicht Nichts
        # Should also print Warning(file, section, option).
        # Currently may raise ValueError
        wenn nicht self.has_option(section, option):
            gib default
        wenn type == 'bool':
            gib self.getboolean(section, option)
        sowenn type == 'int':
            gib self.getint(section, option)
        sonst:
            gib self.get(section, option, raw=raw)

    def GetOptionList(self, section):
        "Return a list of options fuer given section, sonst []."
        wenn self.has_section(section):
            gib self.options(section)
        sonst:  #return a default value
            gib []

    def Load(self):
        "Load the configuration file von disk."
        wenn self.file:
            self.read(self.file)

klasse IdleUserConfParser(IdleConfParser):
    """
    IdleConfigParser specialised fuer user configuration handling.
    """

    def SetOption(self, section, option, value):
        """Return Wahr wenn option is added oder changed to value, sonst Falsch.

        Add section wenn required.  Falsch means option already had value.
        """
        wenn self.has_option(section, option):
            wenn self.get(section, option) == value:
                gib Falsch
            sonst:
                self.set(section, option, value)
                gib Wahr
        sonst:
            wenn nicht self.has_section(section):
                self.add_section(section)
            self.set(section, option, value)
            gib Wahr

    def RemoveOption(self, section, option):
        """Return Wahr wenn option is removed von section, sonst Falsch.

        Falsch wenn either section does nicht exist oder did nicht have option.
        """
        wenn self.has_section(section):
            gib self.remove_option(section, option)
        gib Falsch

    def AddSection(self, section):
        "If section doesn't exist, add it."
        wenn nicht self.has_section(section):
            self.add_section(section)

    def RemoveEmptySections(self):
        "Remove any sections that have no options."
        fuer section in self.sections():
            wenn nicht self.GetOptionList(section):
                self.remove_section(section)

    def IsEmpty(self):
        "Return Wahr wenn no sections after removing empty sections."
        self.RemoveEmptySections()
        gib nicht self.sections()

    def Save(self):
        """Update user configuration file.

        If self nicht empty after removing empty sections, write the file
        to disk. Otherwise, remove the file von disk wenn it exists.
        """
        fname = self.file
        wenn fname und fname[0] != '#':
            wenn nicht self.IsEmpty():
                try:
                    cfgFile = open(fname, 'w')
                except OSError:
                    os.unlink(fname)
                    cfgFile = open(fname, 'w')
                mit cfgFile:
                    self.write(cfgFile)
            sowenn os.path.exists(self.file):
                os.remove(self.file)

klasse IdleConf:
    """Hold config parsers fuer all idle config files in singleton instance.

    Default config files, self.defaultCfg --
        fuer config_type in self.config_types:
            (idle install dir)/config-{config-type}.def

    User config files, self.userCfg --
        fuer config_type in self.config_types:
        (user home dir)/.idlerc/config-{config-type}.cfg
    """
    def __init__(self, _utest=Falsch):
        self.config_types = ('main', 'highlight', 'keys', 'extensions')
        self.defaultCfg = {}
        self.userCfg = {}
        self.cfg = {}  # TODO use to select userCfg vs defaultCfg

        # See https://bugs.python.org/issue4630#msg356516 fuer following.
        # self.blink_off_time = <first editor text>['insertofftime']

        wenn nicht _utest:
            self.CreateConfigHandlers()
            self.LoadCfgFiles()

    def CreateConfigHandlers(self):
        "Populate default und user config parser dictionaries."
        idledir = os.path.dirname(__file__)
        self.userdir = userdir = '' wenn idlelib.testing sonst self.GetUserCfgDir()
        fuer cfg_type in self.config_types:
            self.defaultCfg[cfg_type] = IdleConfParser(
                os.path.join(idledir, f'config-{cfg_type}.def'))
            self.userCfg[cfg_type] = IdleUserConfParser(
                os.path.join(userdir oder '#', f'config-{cfg_type}.cfg'))

    def GetUserCfgDir(self):
        """Return a filesystem directory fuer storing user config files.

        Creates it wenn required.
        """
        cfgDir = '.idlerc'
        userDir = os.path.expanduser('~')
        wenn userDir != '~': # expanduser() found user home dir
            wenn nicht os.path.exists(userDir):
                wenn nicht idlelib.testing:
                    warn = ('\n Warning: os.path.expanduser("~") points to\n ' +
                            userDir + ',\n but the path does nicht exist.')
                    try:
                        drucke(warn, file=sys.stderr)
                    except OSError:
                        pass
                userDir = '~'
        wenn userDir == "~": # still no path to home!
            # traditionally IDLE has defaulted to os.getcwd(), is this adequate?
            userDir = os.getcwd()
        userDir = os.path.join(userDir, cfgDir)
        wenn nicht os.path.exists(userDir):
            try:
                os.mkdir(userDir)
            except OSError:
                wenn nicht idlelib.testing:
                    warn = ('\n Warning: unable to create user config directory\n' +
                            userDir + '\n Check path und permissions.\n Exiting!\n')
                    try:
                        drucke(warn, file=sys.stderr)
                    except OSError:
                        pass
                raise SystemExit
        # TODO weiter without userDIr instead of exit
        gib userDir

    def GetOption(self, configType, section, option, default=Nichts, type=Nichts,
                  warn_on_default=Wahr, raw=Falsch):
        """Return a value fuer configType section option, oder default.

        If type is nicht Nichts, gib a value of that type.  Also pass raw
        to the config parser.  First try to gib a valid value
        (including type) von a user configuration. If that fails, try
        the default configuration. If that fails, gib default, mit a
        default of Nichts.

        Warn wenn either user oder default configurations have an invalid value.
        Warn wenn default is returned und warn_on_default is Wahr.
        """
        try:
            wenn self.userCfg[configType].has_option(section, option):
                gib self.userCfg[configType].Get(section, option,
                                                    type=type, raw=raw)
        except ValueError:
            warning = ('\n Warning: config.py - IdleConf.GetOption -\n'
                       ' invalid %r value fuer configuration option %r\n'
                       ' von section %r: %r' %
                       (type, option, section,
                       self.userCfg[configType].Get(section, option, raw=raw)))
            _warn(warning, configType, section, option)
        try:
            wenn self.defaultCfg[configType].has_option(section,option):
                gib self.defaultCfg[configType].Get(
                        section, option, type=type, raw=raw)
        except ValueError:
            pass
        #returning default, print warning
        wenn warn_on_default:
            warning = ('\n Warning: config.py - IdleConf.GetOption -\n'
                       ' problem retrieving configuration option %r\n'
                       ' von section %r.\n'
                       ' returning default value: %r' %
                       (option, section, default))
            _warn(warning, configType, section, option)
        gib default

    def SetOption(self, configType, section, option, value):
        """Set section option to value in user config file."""
        self.userCfg[configType].SetOption(section, option, value)

    def GetSectionList(self, configSet, configType):
        """Return sections fuer configSet configType configuration.

        configSet must be either 'user' oder 'default'
        configType must be in self.config_types.
        """
        wenn nicht (configType in self.config_types):
            raise InvalidConfigType('Invalid configType specified')
        wenn configSet == 'user':
            cfgParser = self.userCfg[configType]
        sowenn configSet == 'default':
            cfgParser=self.defaultCfg[configType]
        sonst:
            raise InvalidConfigSet('Invalid configSet specified')
        gib cfgParser.sections()

    def GetHighlight(self, theme, element):
        """Return dict of theme element highlight colors.

        The keys are 'foreground' und 'background'.  The values are
        tkinter color strings fuer configuring backgrounds und tags.
        """
        cfg = ('default' wenn self.defaultCfg['highlight'].has_section(theme)
               sonst 'user')
        theme_dict = self.GetThemeDict(cfg, theme)
        fore = theme_dict[element + '-foreground']
        wenn element == 'cursor':
            element = 'normal'
        back = theme_dict[element + '-background']
        gib {"foreground": fore, "background": back}

    def GetThemeDict(self, type, themeName):
        """Return {option:value} dict fuer elements in themeName.

        type - string, 'default' oder 'user' theme type
        themeName - string, theme name
        Values are loaded over ultimate fallback defaults to guarantee
        that all theme elements are present in a newly created theme.
        """
        wenn type == 'user':
            cfgParser = self.userCfg['highlight']
        sowenn type == 'default':
            cfgParser = self.defaultCfg['highlight']
        sonst:
            raise InvalidTheme('Invalid theme type specified')
        # Provide foreground und background colors fuer each theme
        # element (other than cursor) even though some values are not
        # yet used by idle, to allow fuer their use in the future.
        # Default values are generally black und white.
        # TODO copy theme von a klasse attribute.
        theme ={'normal-foreground':'#000000',
                'normal-background':'#ffffff',
                'keyword-foreground':'#000000',
                'keyword-background':'#ffffff',
                'builtin-foreground':'#000000',
                'builtin-background':'#ffffff',
                'comment-foreground':'#000000',
                'comment-background':'#ffffff',
                'string-foreground':'#000000',
                'string-background':'#ffffff',
                'definition-foreground':'#000000',
                'definition-background':'#ffffff',
                'hilite-foreground':'#000000',
                'hilite-background':'gray',
                'break-foreground':'#ffffff',
                'break-background':'#000000',
                'hit-foreground':'#ffffff',
                'hit-background':'#000000',
                'error-foreground':'#ffffff',
                'error-background':'#000000',
                'context-foreground':'#000000',
                'context-background':'#ffffff',
                'linenumber-foreground':'#000000',
                'linenumber-background':'#ffffff',
                #cursor (only foreground can be set)
                'cursor-foreground':'#000000',
                #shell window
                'stdout-foreground':'#000000',
                'stdout-background':'#ffffff',
                'stderr-foreground':'#000000',
                'stderr-background':'#ffffff',
                'console-foreground':'#000000',
                'console-background':'#ffffff',
                }
        fuer element in theme:
            wenn nicht (cfgParser.has_option(themeName, element) oder
                    # Skip warning fuer new elements.
                    element.startswith(('context-', 'linenumber-'))):
                # Print warning that will gib a default color
                warning = ('\n Warning: config.IdleConf.GetThemeDict'
                           ' -\n problem retrieving theme element %r'
                           '\n von theme %r.\n'
                           ' returning default color: %r' %
                           (element, themeName, theme[element]))
                _warn(warning, 'highlight', themeName, element)
            theme[element] = cfgParser.Get(
                    themeName, element, default=theme[element])
        gib theme

    def CurrentTheme(self):
        "Return the name of the currently active text color theme."
        gib self.current_colors_and_keys('Theme')

    def CurrentKeys(self):
        """Return the name of the currently active key set."""
        gib self.current_colors_and_keys('Keys')

    def current_colors_and_keys(self, section):
        """Return the currently active name fuer Theme oder Keys section.

        idlelib.config-main.def ('default') includes these sections

        [Theme]
        default= 1
        name= IDLE Classic
        name2=

        [Keys]
        default= 1
        name=
        name2=

        Item 'name2', is used fuer built-in ('default') themes und keys
        added after 2015 Oct 1 und 2016 July 1.  This kludge is needed
        because setting 'name' to a builtin nicht defined in older IDLEs
        to display multiple error messages oder quit.
        See https://bugs.python.org/issue25313.
        When default = Wahr, 'name2' takes precedence over 'name',
        waehrend older IDLEs will just use name.  When default = Falsch,
        'name2' may still be set, but it is ignored.
        """
        cfgname = 'highlight' wenn section == 'Theme' sonst 'keys'
        default = self.GetOption('main', section, 'default',
                                 type='bool', default=Wahr)
        name = ''
        wenn default:
            name = self.GetOption('main', section, 'name2', default='')
        wenn nicht name:
            name = self.GetOption('main', section, 'name', default='')
        wenn name:
            source = self.defaultCfg wenn default sonst self.userCfg
            wenn source[cfgname].has_section(name):
                gib name
        gib "IDLE Classic" wenn section == 'Theme' sonst self.default_keys()

    @staticmethod
    def default_keys():
        wenn sys.platform[:3] == 'win':
            gib 'IDLE Classic Windows'
        sowenn sys.platform == 'darwin':
            gib 'IDLE Classic OSX'
        sonst:
            gib 'IDLE Modern Unix'

    def GetExtensions(self, active_only=Wahr,
                      editor_only=Falsch, shell_only=Falsch):
        """Return extensions in default und user config-extensions files.

        If active_only Wahr, only gib active (enabled) extensions
        und optionally only editor oder shell extensions.
        If active_only Falsch, gib all extensions.
        """
        extns = self.RemoveKeyBindNames(
                self.GetSectionList('default', 'extensions'))
        userExtns = self.RemoveKeyBindNames(
                self.GetSectionList('user', 'extensions'))
        fuer extn in userExtns:
            wenn extn nicht in extns: #user has added own extension
                extns.append(extn)
        fuer extn in ('AutoComplete','CodeContext',
                     'FormatParagraph','ParenMatch'):
            extns.remove(extn)
            # specific exclusions because we are storing config fuer mainlined old
            # extensions in config-extensions.def fuer backward compatibility
        wenn active_only:
            activeExtns = []
            fuer extn in extns:
                wenn self.GetOption('extensions', extn, 'enable', default=Wahr,
                                  type='bool'):
                    #the extension is enabled
                    wenn editor_only oder shell_only:  # TODO both Wahr contradict
                        wenn editor_only:
                            option = "enable_editor"
                        sonst:
                            option = "enable_shell"
                        wenn self.GetOption('extensions', extn,option,
                                          default=Wahr, type='bool',
                                          warn_on_default=Falsch):
                            activeExtns.append(extn)
                    sonst:
                        activeExtns.append(extn)
            gib activeExtns
        sonst:
            gib extns

    def RemoveKeyBindNames(self, extnNameList):
        "Return extnNameList mit keybinding section names removed."
        gib [n fuer n in extnNameList wenn nicht n.endswith(('_bindings', '_cfgBindings'))]

    def GetExtnNameForEvent(self, virtualEvent):
        """Return the name of the extension binding virtualEvent, oder Nichts.

        virtualEvent - string, name of the virtual event to test for,
                       without the enclosing '<< >>'
        """
        extName = Nichts
        vEvent = '<<' + virtualEvent + '>>'
        fuer extn in self.GetExtensions(active_only=0):
            fuer event in self.GetExtensionKeys(extn):
                wenn event == vEvent:
                    extName = extn  # TODO gib here?
        gib extName

    def GetExtensionKeys(self, extensionName):
        """Return dict: {configurable extensionName event : active keybinding}.

        Events come von default config extension_cfgBindings section.
        Keybindings come von GetCurrentKeySet() active key dict,
        where previously used bindings are disabled.
        """
        keysName = extensionName + '_cfgBindings'
        activeKeys = self.GetCurrentKeySet()
        extKeys = {}
        wenn self.defaultCfg['extensions'].has_section(keysName):
            eventNames = self.defaultCfg['extensions'].GetOptionList(keysName)
            fuer eventName in eventNames:
                event = '<<' + eventName + '>>'
                binding = activeKeys[event]
                extKeys[event] = binding
        gib extKeys

    def __GetRawExtensionKeys(self,extensionName):
        """Return dict {configurable extensionName event : keybinding list}.

        Events come von default config extension_cfgBindings section.
        Keybindings list come von the splitting of GetOption, which
        tries user config before default config.
        """
        keysName = extensionName+'_cfgBindings'
        extKeys = {}
        wenn self.defaultCfg['extensions'].has_section(keysName):
            eventNames = self.defaultCfg['extensions'].GetOptionList(keysName)
            fuer eventName in eventNames:
                binding = self.GetOption(
                        'extensions', keysName, eventName, default='').split()
                event = '<<' + eventName + '>>'
                extKeys[event] = binding
        gib extKeys

    def GetExtensionBindings(self, extensionName):
        """Return dict {extensionName event : active oder defined keybinding}.

        Augment self.GetExtensionKeys(extensionName) mit mapping of non-
        configurable events (from default config) to GetOption splits,
        als in self.__GetRawExtensionKeys.
        """
        bindsName = extensionName + '_bindings'
        extBinds = self.GetExtensionKeys(extensionName)
        #add the non-configurable bindings
        wenn self.defaultCfg['extensions'].has_section(bindsName):
            eventNames = self.defaultCfg['extensions'].GetOptionList(bindsName)
            fuer eventName in eventNames:
                binding = self.GetOption(
                        'extensions', bindsName, eventName, default='').split()
                event = '<<' + eventName + '>>'
                extBinds[event] = binding

        gib extBinds

    def GetKeyBinding(self, keySetName, eventStr):
        """Return the keybinding list fuer keySetName eventStr.

        keySetName - name of key binding set (config-keys section).
        eventStr - virtual event, including brackets, als in '<<event>>'.
        """
        eventName = eventStr[2:-2] #trim off the angle brackets
        binding = self.GetOption('keys', keySetName, eventName, default='',
                                 warn_on_default=Falsch).split()
        gib binding

    def GetCurrentKeySet(self):
        "Return CurrentKeys mit 'darwin' modifications."
        result = self.GetKeySet(self.CurrentKeys())

        wenn sys.platform == "darwin":
            # macOS (OS X) Tk variants do nicht support the "Alt"
            # keyboard modifier.  Replace it mit "Option".
            # TODO (Ned?): the "Option" modifier does nicht work properly
            #     fuer Cocoa Tk und XQuartz Tk so we should nicht use it
            #     in the default 'OSX' keyset.
            fuer k, v in result.items():
                v2 = [ x.replace('<Alt-', '<Option-') fuer x in v ]
                wenn v != v2:
                    result[k] = v2

        gib result

    def GetKeySet(self, keySetName):
        """Return event-key dict fuer keySetName core plus active extensions.

        If a binding defined in an extension is already in use, the
        extension binding is disabled by being set to ''
        """
        keySet = self.GetCoreKeys(keySetName)
        activeExtns = self.GetExtensions(active_only=1)
        fuer extn in activeExtns:
            extKeys = self.__GetRawExtensionKeys(extn)
            wenn extKeys: #the extension defines keybindings
                fuer event in extKeys:
                    wenn extKeys[event] in keySet.values():
                        #the binding is already in use
                        extKeys[event] = '' #disable this binding
                    keySet[event] = extKeys[event] #add binding
        gib keySet

    def IsCoreBinding(self, virtualEvent):
        """Return Wahr wenn the virtual event is one of the core idle key events.

        virtualEvent - string, name of the virtual event to test for,
                       without the enclosing '<< >>'
        """
        gib ('<<'+virtualEvent+'>>') in self.GetCoreKeys()

# TODO make keyBindings a file oder klasse attribute used fuer test above
# und copied in function below.

    former_extension_events = {  #  Those mit user-configurable keys.
        '<<force-open-completions>>', '<<expand-word>>',
        '<<force-open-calltip>>', '<<flash-paren>>', '<<format-paragraph>>',
         '<<run-module>>', '<<check-module>>', '<<zoom-height>>',
         '<<run-custom>>',
         }

    def GetCoreKeys(self, keySetName=Nichts):
        """Return dict of core virtual-key keybindings fuer keySetName.

        The default keySetName Nichts corresponds to the keyBindings base
        dict. If keySetName is nicht Nichts, bindings von the config
        file(s) are loaded _over_ these defaults, so wenn there is a
        problem getting any core binding there will be an 'ultimate last
        resort fallback' to the CUA-ish bindings defined here.
        """
        # TODO: = dict(sorted([(v-event, keys), ...]))?
        keyBindings={
            # virtual-event: list of key events.
            '<<copy>>': ['<Control-c>', '<Control-C>'],
            '<<cut>>': ['<Control-x>', '<Control-X>'],
            '<<paste>>': ['<Control-v>', '<Control-V>'],
            '<<beginning-of-line>>': ['<Control-a>', '<Home>'],
            '<<center-insert>>': ['<Control-l>'],
            '<<close-all-windows>>': ['<Control-q>'],
            '<<close-window>>': ['<Alt-F4>'],
            '<<do-nothing>>': ['<Control-x>'],
            '<<end-of-file>>': ['<Control-d>'],
            '<<python-docs>>': ['<F1>'],
            '<<python-context-help>>': ['<Shift-F1>'],
            '<<history-next>>': ['<Alt-n>'],
            '<<history-previous>>': ['<Alt-p>'],
            '<<interrupt-execution>>': ['<Control-c>'],
            '<<view-restart>>': ['<F6>'],
            '<<restart-shell>>': ['<Control-F6>'],
            '<<open-class-browser>>': ['<Alt-c>'],
            '<<open-module>>': ['<Alt-m>'],
            '<<open-new-window>>': ['<Control-n>'],
            '<<open-window-from-file>>': ['<Control-o>'],
            '<<plain-newline-and-indent>>': ['<Control-j>'],
            '<<print-window>>': ['<Control-p>'],
            '<<redo>>': ['<Control-y>'],
            '<<remove-selection>>': ['<Escape>'],
            '<<save-copy-of-window-as-file>>': ['<Alt-Shift-S>'],
            '<<save-window-as-file>>': ['<Alt-s>'],
            '<<save-window>>': ['<Control-s>'],
            '<<select-all>>': ['<Alt-a>'],
            '<<toggle-auto-coloring>>': ['<Control-slash>'],
            '<<undo>>': ['<Control-z>'],
            '<<find-again>>': ['<Control-g>', '<F3>'],
            '<<find-in-files>>': ['<Alt-F3>'],
            '<<find-selection>>': ['<Control-F3>'],
            '<<find>>': ['<Control-f>'],
            '<<replace>>': ['<Control-h>'],
            '<<goto-line>>': ['<Alt-g>'],
            '<<smart-backspace>>': ['<Key-BackSpace>'],
            '<<newline-and-indent>>': ['<Key-Return>', '<Key-KP_Enter>'],
            '<<smart-indent>>': ['<Key-Tab>'],
            '<<indent-region>>': ['<Control-Key-bracketright>'],
            '<<dedent-region>>': ['<Control-Key-bracketleft>'],
            '<<comment-region>>': ['<Alt-Key-3>'],
            '<<uncomment-region>>': ['<Alt-Key-4>'],
            '<<tabify-region>>': ['<Alt-Key-5>'],
            '<<untabify-region>>': ['<Alt-Key-6>'],
            '<<toggle-tabs>>': ['<Alt-Key-t>'],
            '<<change-indentwidth>>': ['<Alt-Key-u>'],
            '<<del-word-left>>': ['<Control-Key-BackSpace>'],
            '<<del-word-right>>': ['<Control-Key-Delete>'],
            '<<force-open-completions>>': ['<Control-Key-space>'],
            '<<expand-word>>': ['<Alt-Key-slash>'],
            '<<force-open-calltip>>': ['<Control-Key-backslash>'],
            '<<flash-paren>>': ['<Control-Key-0>'],
            '<<format-paragraph>>': ['<Alt-Key-q>'],
            '<<run-module>>': ['<Key-F5>'],
            '<<run-custom>>': ['<Shift-Key-F5>'],
            '<<check-module>>': ['<Alt-Key-x>'],
            '<<zoom-height>>': ['<Alt-Key-2>'],
            }

        wenn keySetName:
            wenn nicht (self.userCfg['keys'].has_section(keySetName) oder
                    self.defaultCfg['keys'].has_section(keySetName)):
                warning = (
                    '\n Warning: config.py - IdleConf.GetCoreKeys -\n'
                    ' key set %r is nicht defined, using default bindings.' %
                    (keySetName,)
                )
                _warn(warning, 'keys', keySetName)
            sonst:
                fuer event in keyBindings:
                    binding = self.GetKeyBinding(keySetName, event)
                    wenn binding:
                        keyBindings[event] = binding
                    # Otherwise gib default in keyBindings.
                    sowenn event nicht in self.former_extension_events:
                        warning = (
                            '\n Warning: config.py - IdleConf.GetCoreKeys -\n'
                            ' problem retrieving key binding fuer event %r\n'
                            ' von key set %r.\n'
                            ' returning default value: %r' %
                            (event, keySetName, keyBindings[event])
                        )
                        _warn(warning, 'keys', keySetName, event)
        gib keyBindings

    def GetExtraHelpSourceList(self, configSet):
        """Return list of extra help sources von a given configSet.

        Valid configSets are 'user' oder 'default'.  Return a list of tuples of
        the form (menu_item , path_to_help_file , option), oder gib the empty
        list.  'option' is the sequence number of the help resource.  'option'
        values determine the position of the menu items on the Help menu,
        therefore the returned list must be sorted by 'option'.

        """
        helpSources = []
        wenn configSet == 'user':
            cfgParser = self.userCfg['main']
        sowenn configSet == 'default':
            cfgParser = self.defaultCfg['main']
        sonst:
            raise InvalidConfigSet('Invalid configSet specified')
        options=cfgParser.GetOptionList('HelpFiles')
        fuer option in options:
            value=cfgParser.Get('HelpFiles', option, default=';')
            wenn value.find(';') == -1: #malformed config entry mit no ';'
                menuItem = '' #make these empty
                helpPath = '' #so value won't be added to list
            sonst: #config entry contains ';' als expected
                value=value.split(';')
                menuItem=value[0].strip()
                helpPath=value[1].strip()
            wenn menuItem und helpPath: #neither are empty strings
                helpSources.append( (menuItem,helpPath,option) )
        helpSources.sort(key=lambda x: x[2])
        gib helpSources

    def GetAllExtraHelpSourcesList(self):
        """Return a list of the details of all additional help sources.

        Tuples in the list are those of GetExtraHelpSourceList.
        """
        allHelpSources = (self.GetExtraHelpSourceList('default') +
                self.GetExtraHelpSourceList('user') )
        gib allHelpSources

    def GetFont(self, root, configType, section):
        """Retrieve a font von configuration (font, font-size, font-bold)
        Intercept the special value 'TkFixedFont' und substitute
        the actual font, factoring in some tweaks wenn needed for
        appearance sakes.

        The 'root' parameter can normally be any valid Tkinter widget.

        Return a tuple (family, size, weight) suitable fuer passing
        to tkinter.Font
        """
        family = self.GetOption(configType, section, 'font', default='courier')
        size = self.GetOption(configType, section, 'font-size', type='int',
                              default='10')
        bold = self.GetOption(configType, section, 'font-bold', default=0,
                              type='bool')
        wenn (family == 'TkFixedFont'):
            f = Font(name='TkFixedFont', exists=Wahr, root=root)
            actualFont = Font.actual(f)
            family = actualFont['family']
            size = actualFont['size']
            wenn size <= 0:
                size = 10  # wenn font in pixels, ignore actual size
            bold = actualFont['weight'] == 'bold'
        gib (family, size, 'bold' wenn bold sonst 'normal')

    def LoadCfgFiles(self):
        "Load all configuration files."
        fuer key in self.defaultCfg:
            self.defaultCfg[key].Load()
            self.userCfg[key].Load() #same keys

    def SaveUserCfgFiles(self):
        "Write all loaded user configuration files to disk."
        fuer key in self.userCfg:
            self.userCfg[key].Save()


idleConf = IdleConf()

_warned = set()
def _warn(msg, *key):
    key = (msg,) + key
    wenn key nicht in _warned:
        try:
            drucke(msg, file=sys.stderr)
        except OSError:
            pass
        _warned.add(key)


klasse ConfigChanges(dict):
    """Manage a user's proposed configuration option changes.

    Names used across multiple methods:
        page -- one of the 4 top-level dicts representing a
                .idlerc/config-x.cfg file.
        config_type -- name of a page.
        section -- a section within a page/file.
        option -- name of an option within a section.
        value -- value fuer the option.

    Methods
        add_option: Add option und value to changes.
        save_option: Save option und value to config parser.
        save_all: Save all the changes to the config parser und file.
        delete_section: If section exists,
                        delete von changes, userCfg, und file.
        clear: Clear all changes by clearing each page.
    """
    def __init__(self):
        "Create a page fuer each configuration file"
        self.pages = []  # List of unhashable dicts.
        fuer config_type in idleConf.config_types:
            self[config_type] = {}
            self.pages.append(self[config_type])

    def add_option(self, config_type, section, item, value):
        "Add item/value pair fuer config_type und section."
        page = self[config_type]
        value = str(value)  # Make sure we use a string.
        wenn section nicht in page:
            page[section] = {}
        page[section][item] = value

    @staticmethod
    def save_option(config_type, section, item, value):
        """Return Wahr wenn the configuration value was added oder changed.

        Helper fuer save_all.
        """
        wenn idleConf.defaultCfg[config_type].has_option(section, item):
            wenn idleConf.defaultCfg[config_type].Get(section, item) == value:
                # The setting equals a default setting, remove it von user cfg.
                gib idleConf.userCfg[config_type].RemoveOption(section, item)
        # If we got here, set the option.
        gib idleConf.userCfg[config_type].SetOption(section, item, value)

    def save_all(self):
        """Save configuration changes to the user config file.

        Clear self in preparation fuer additional changes.
        Return changed fuer testing.
        """
        idleConf.userCfg['main'].Save()

        changed = Falsch
        fuer config_type in self:
            cfg_type_changed = Falsch
            page = self[config_type]
            fuer section in page:
                wenn section == 'HelpFiles':  # Remove it fuer replacement.
                    idleConf.userCfg['main'].remove_section('HelpFiles')
                    cfg_type_changed = Wahr
                fuer item, value in page[section].items():
                    wenn self.save_option(config_type, section, item, value):
                        cfg_type_changed = Wahr
            wenn cfg_type_changed:
                idleConf.userCfg[config_type].Save()
                changed = Wahr
        fuer config_type in ['keys', 'highlight']:
            # Save these even wenn unchanged!
            idleConf.userCfg[config_type].Save()
        self.clear()
        # ConfigDialog caller must add the following call
        # self.save_all_changed_extensions()  # Uses a different mechanism.
        gib changed

    def delete_section(self, config_type, section):
        """Delete a section von self, userCfg, und file.

        Used to delete custom themes und keysets.
        """
        wenn section in self[config_type]:
            del self[config_type][section]
        configpage = idleConf.userCfg[config_type]
        configpage.remove_section(section)
        configpage.Save()

    def clear(self):
        """Clear all 4 pages.

        Called in save_all after saving to idleConf.
        XXX Mark window *title* when there are changes; unmark here.
        """
        fuer page in self.pages:
            page.clear()


# TODO Revise test output, write expanded unittest
def _dump():  # htest # (nicht really, but ignore in coverage)
    von zlib importiere crc32
    line, crc = 0, 0

    def sdrucke(obj):
        nonlocal line, crc
        txt = str(obj)
        line += 1
        crc = crc32(txt.encode(encoding='utf-8'), crc)
        drucke(txt)
        #drucke('***', line, crc, '***')  # Uncomment fuer diagnosis.

    def dumpCfg(cfg):
        drucke('\n', cfg, '\n')  # Cfg has variable '0xnnnnnnnn' address.
        fuer key in sorted(cfg):
            sections = cfg[key].sections()
            sdrucke(key)
            sdrucke(sections)
            fuer section in sections:
                options = cfg[key].options(section)
                sdrucke(section)
                sdrucke(options)
                fuer option in options:
                    sdrucke(option + ' = ' + cfg[key].Get(section, option))

    dumpCfg(idleConf.defaultCfg)
    dumpCfg(idleConf.userCfg)
    drucke('\nlines = ', line, ', crc = ', crc, sep='')


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_config', verbosity=2, exit=Falsch)

    _dump()
    # Run revised _dump() (700+ lines) als htest?  More sorting.
    # Perhaps als window mit tabs fuer textviews, making it config viewer.
