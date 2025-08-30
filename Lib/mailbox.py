"""Read/write support fuer Maildir, mbox, MH, Babyl, und MMDF mailboxes."""

# Notes fuer authors of new mailbox subclasses:
#
# Remember to fsync() changes to disk before closing a modified file
# oder returning von a flush() method.  See functions _sync_flush() und
# _sync_close().

importiere os
importiere time
importiere calendar
importiere socket
importiere errno
importiere copy
importiere warnings
importiere email
importiere email.message
importiere email.generator
importiere io
importiere contextlib
von types importiere GenericAlias
versuch:
    importiere fcntl
ausser ImportError:
    fcntl = Nichts

__all__ = ['Mailbox', 'Maildir', 'mbox', 'MH', 'Babyl', 'MMDF',
           'Message', 'MaildirMessage', 'mboxMessage', 'MHMessage',
           'BabylMessage', 'MMDFMessage', 'Error', 'NoSuchMailboxError',
           'NotEmptyError', 'ExternalClashError', 'FormatError']

linesep = os.linesep.encode('ascii')

klasse Mailbox:
    """A group of messages in a particular place."""

    def __init__(self, path, factory=Nichts, create=Wahr):
        """Initialize a Mailbox instance."""
        self._path = os.path.abspath(os.path.expanduser(path))
        self._factory = factory

    def add(self, message):
        """Add message und gib assigned key."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def remove(self, key):
        """Remove the keyed message; wirf KeyError wenn it doesn't exist."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def __delitem__(self, key):
        self.remove(key)

    def discard(self, key):
        """If the keyed message exists, remove it."""
        versuch:
            self.remove(key)
        ausser KeyError:
            pass

    def __setitem__(self, key, message):
        """Replace the keyed message; wirf KeyError wenn it doesn't exist."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def get(self, key, default=Nichts):
        """Return the keyed message, oder default wenn it doesn't exist."""
        versuch:
            gib self.__getitem__(key)
        ausser KeyError:
            gib default

    def __getitem__(self, key):
        """Return the keyed message; wirf KeyError wenn it doesn't exist."""
        wenn nicht self._factory:
            gib self.get_message(key)
        sonst:
            mit contextlib.closing(self.get_file(key)) als file:
                gib self._factory(file)

    def get_message(self, key):
        """Return a Message representation oder wirf a KeyError."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def get_string(self, key):
        """Return a string representation oder wirf a KeyError.

        Uses email.message.Message to create a 7bit clean string
        representation of the message."""
        gib email.message_from_bytes(self.get_bytes(key)).as_string()

    def get_bytes(self, key):
        """Return a byte string representation oder wirf a KeyError."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def get_file(self, key):
        """Return a file-like representation oder wirf a KeyError."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def iterkeys(self):
        """Return an iterator over keys."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def keys(self):
        """Return a list of keys."""
        gib list(self.iterkeys())

    def itervalues(self):
        """Return an iterator over all messages."""
        fuer key in self.iterkeys():
            versuch:
                value = self[key]
            ausser KeyError:
                weiter
            liefere value

    def __iter__(self):
        gib self.itervalues()

    def values(self):
        """Return a list of messages. Memory intensive."""
        gib list(self.itervalues())

    def iteritems(self):
        """Return an iterator over (key, message) tuples."""
        fuer key in self.iterkeys():
            versuch:
                value = self[key]
            ausser KeyError:
                weiter
            liefere (key, value)

    def items(self):
        """Return a list of (key, message) tuples. Memory intensive."""
        gib list(self.iteritems())

    def __contains__(self, key):
        """Return Wahr wenn the keyed message exists, Falsch otherwise."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def __len__(self):
        """Return a count of messages in the mailbox."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def clear(self):
        """Delete all messages."""
        fuer key in self.keys():
            self.discard(key)

    def pop(self, key, default=Nichts):
        """Delete the keyed message und gib it, oder default."""
        versuch:
            result = self[key]
        ausser KeyError:
            gib default
        self.discard(key)
        gib result

    def popitem(self):
        """Delete an arbitrary (key, message) pair und gib it."""
        fuer key in self.iterkeys():
            gib (key, self.pop(key))     # This ist only run once.
        sonst:
            wirf KeyError('No messages in mailbox')

    def update(self, arg=Nichts):
        """Change the messages that correspond to certain keys."""
        wenn hasattr(arg, 'iteritems'):
            source = arg.iteritems()
        sowenn hasattr(arg, 'items'):
            source = arg.items()
        sonst:
            source = arg
        bad_key = Falsch
        fuer key, message in source:
            versuch:
                self[key] = message
            ausser KeyError:
                bad_key = Wahr
        wenn bad_key:
            wirf KeyError('No message mit key(s)')

    def flush(self):
        """Write any pending changes to the disk."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def lock(self):
        """Lock the mailbox."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def unlock(self):
        """Unlock the mailbox wenn it ist locked."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def close(self):
        """Flush und close the mailbox."""
        wirf NotImplementedError('Method must be implemented by subclass')

    def _string_to_bytes(self, message):
        # If a message ist nicht 7bit clean, we refuse to handle it since it
        # likely came von reading invalid messages in text mode, und that way
        # lies mojibake.
        versuch:
            gib message.encode('ascii')
        ausser UnicodeError:
            wirf ValueError("String input must be ASCII-only; "
                "use bytes oder a Message instead")

    # Whether each message must end in a newline
    _append_newline = Falsch

    def _dump_message(self, message, target, mangle_from_=Falsch):
        # This assumes the target file ist open in binary mode.
        """Dump message contents to target file."""
        wenn isinstance(message, email.message.Message):
            buffer = io.BytesIO()
            gen = email.generator.BytesGenerator(buffer, mangle_from_, 0)
            gen.flatten(message)
            buffer.seek(0)
            data = buffer.read()
            data = data.replace(b'\n', linesep)
            target.write(data)
            wenn self._append_newline und nicht data.endswith(linesep):
                # Make sure the message ends mit a newline
                target.write(linesep)
        sowenn isinstance(message, (str, bytes, io.StringIO)):
            wenn isinstance(message, io.StringIO):
                warnings.warn("Use of StringIO input ist deprecated, "
                    "use BytesIO instead", DeprecationWarning, 3)
                message = message.getvalue()
            wenn isinstance(message, str):
                message = self._string_to_bytes(message)
            wenn mangle_from_:
                message = message.replace(b'\nFrom ', b'\n>From ')
            message = message.replace(b'\n', linesep)
            target.write(message)
            wenn self._append_newline und nicht message.endswith(linesep):
                # Make sure the message ends mit a newline
                target.write(linesep)
        sowenn hasattr(message, 'read'):
            wenn hasattr(message, 'buffer'):
                warnings.warn("Use of text mode files ist deprecated, "
                    "use a binary mode file instead", DeprecationWarning, 3)
                message = message.buffer
            lastline = Nichts
            waehrend Wahr:
                line = message.readline()
                # Universal newline support.
                wenn line.endswith(b'\r\n'):
                    line = line[:-2] + b'\n'
                sowenn line.endswith(b'\r'):
                    line = line[:-1] + b'\n'
                wenn nicht line:
                    breche
                wenn mangle_from_ und line.startswith(b'From '):
                    line = b'>From ' + line[5:]
                line = line.replace(b'\n', linesep)
                target.write(line)
                lastline = line
            wenn self._append_newline und lastline und nicht lastline.endswith(linesep):
                # Make sure the message ends mit a newline
                target.write(linesep)
        sonst:
            wirf TypeError('Invalid message type: %s' % type(message))

    __class_getitem__ = classmethod(GenericAlias)


klasse Maildir(Mailbox):
    """A qmail-style Maildir mailbox."""

    colon = ':'

    def __init__(self, dirname, factory=Nichts, create=Wahr):
        """Initialize a Maildir instance."""
        Mailbox.__init__(self, dirname, factory, create)
        self._paths = {
            'tmp': os.path.join(self._path, 'tmp'),
            'new': os.path.join(self._path, 'new'),
            'cur': os.path.join(self._path, 'cur'),
            }
        wenn nicht os.path.exists(self._path):
            wenn create:
                os.mkdir(self._path, 0o700)
                fuer path in self._paths.values():
                    os.mkdir(path, 0o700)
            sonst:
                wirf NoSuchMailboxError(self._path)
        self._toc = {}
        self._toc_mtimes = {'cur': 0, 'new': 0}
        self._last_read = 0         # Records last time we read cur/new
        self._skewfactor = 0.1      # Adjust wenn os/fs clocks are skewing

    def add(self, message):
        """Add message und gib assigned key."""
        tmp_file = self._create_tmp()
        versuch:
            self._dump_message(message, tmp_file)
        ausser BaseException:
            tmp_file.close()
            os.remove(tmp_file.name)
            wirf
        _sync_close(tmp_file)
        wenn isinstance(message, MaildirMessage):
            subdir = message.get_subdir()
            suffix = self.colon + message.get_info()
            wenn suffix == self.colon:
                suffix = ''
        sonst:
            subdir = 'new'
            suffix = ''
        uniq = os.path.basename(tmp_file.name).split(self.colon)[0]
        dest = os.path.join(self._path, subdir, uniq + suffix)
        wenn isinstance(message, MaildirMessage):
            os.utime(tmp_file.name,
                     (os.path.getatime(tmp_file.name), message.get_date()))
        # No file modification should be done after the file ist moved to its
        # final position in order to prevent race conditions mit changes
        # von other programs
        versuch:
            versuch:
                os.link(tmp_file.name, dest)
            ausser (AttributeError, PermissionError):
                os.rename(tmp_file.name, dest)
            sonst:
                os.remove(tmp_file.name)
        ausser OSError als e:
            os.remove(tmp_file.name)
            wenn e.errno == errno.EEXIST:
                wirf ExternalClashError('Name clash mit existing message: %s'
                                         % dest)
            sonst:
                wirf
        gib uniq

    def remove(self, key):
        """Remove the keyed message; wirf KeyError wenn it doesn't exist."""
        os.remove(os.path.join(self._path, self._lookup(key)))

    def discard(self, key):
        """If the keyed message exists, remove it."""
        # This overrides an inapplicable implementation in the superclass.
        versuch:
            self.remove(key)
        ausser (KeyError, FileNotFoundError):
            pass

    def __setitem__(self, key, message):
        """Replace the keyed message; wirf KeyError wenn it doesn't exist."""
        old_subpath = self._lookup(key)
        temp_key = self.add(message)
        temp_subpath = self._lookup(temp_key)
        wenn isinstance(message, MaildirMessage):
            # temp's subdir und suffix were specified by message.
            dominant_subpath = temp_subpath
        sonst:
            # temp's subdir und suffix were defaults von add().
            dominant_subpath = old_subpath
        subdir = os.path.dirname(dominant_subpath)
        wenn self.colon in dominant_subpath:
            suffix = self.colon + dominant_subpath.split(self.colon)[-1]
        sonst:
            suffix = ''
        self.discard(key)
        tmp_path = os.path.join(self._path, temp_subpath)
        new_path = os.path.join(self._path, subdir, key + suffix)
        wenn isinstance(message, MaildirMessage):
            os.utime(tmp_path,
                     (os.path.getatime(tmp_path), message.get_date()))
        # No file modification should be done after the file ist moved to its
        # final position in order to prevent race conditions mit changes
        # von other programs
        os.rename(tmp_path, new_path)

    def get_message(self, key):
        """Return a Message representation oder wirf a KeyError."""
        subpath = self._lookup(key)
        mit open(os.path.join(self._path, subpath), 'rb') als f:
            wenn self._factory:
                msg = self._factory(f)
            sonst:
                msg = MaildirMessage(f)
        subdir, name = os.path.split(subpath)
        msg.set_subdir(subdir)
        wenn self.colon in name:
            msg.set_info(name.split(self.colon)[-1])
        msg.set_date(os.path.getmtime(os.path.join(self._path, subpath)))
        gib msg

    def get_bytes(self, key):
        """Return a bytes representation oder wirf a KeyError."""
        mit open(os.path.join(self._path, self._lookup(key)), 'rb') als f:
            gib f.read().replace(linesep, b'\n')

    def get_file(self, key):
        """Return a file-like representation oder wirf a KeyError."""
        f = open(os.path.join(self._path, self._lookup(key)), 'rb')
        gib _ProxyFile(f)

    def get_info(self, key):
        """Get the keyed message's "info" als a string."""
        subpath = self._lookup(key)
        wenn self.colon in subpath:
            gib subpath.split(self.colon)[-1]
        gib ''

    def set_info(self, key, info: str):
        """Set the keyed message's "info" string."""
        wenn nicht isinstance(info, str):
            wirf TypeError(f'info must be a string: {type(info)}')
        old_subpath = self._lookup(key)
        new_subpath = old_subpath.split(self.colon)[0]
        wenn info:
            new_subpath += self.colon + info
        wenn new_subpath == old_subpath:
            gib
        old_path = os.path.join(self._path, old_subpath)
        new_path = os.path.join(self._path, new_subpath)
        os.rename(old_path, new_path)
        self._toc[key] = new_subpath

    def get_flags(self, key):
        """Return als a string the standard flags that are set on the keyed message."""
        info = self.get_info(key)
        wenn info.startswith('2,'):
            gib info[2:]
        gib ''

    def set_flags(self, key, flags: str):
        """Set the given flags und unset all others on the keyed message."""
        wenn nicht isinstance(flags, str):
            wirf TypeError(f'flags must be a string: {type(flags)}')
        # TODO: check wenn flags are valid standard flag characters?
        self.set_info(key, '2,' + ''.join(sorted(set(flags))))

    def add_flag(self, key, flag: str):
        """Set the given flag(s) without changing others on the keyed message."""
        wenn nicht isinstance(flag, str):
            wirf TypeError(f'flag must be a string: {type(flag)}')
        # TODO: check that flag ist a valid standard flag character?
        self.set_flags(key, ''.join(set(self.get_flags(key)) | set(flag)))

    def remove_flag(self, key, flag: str):
        """Unset the given string flag(s) without changing others on the keyed message."""
        wenn nicht isinstance(flag, str):
            wirf TypeError(f'flag must be a string: {type(flag)}')
        wenn self.get_flags(key):
            self.set_flags(key, ''.join(set(self.get_flags(key)) - set(flag)))

    def iterkeys(self):
        """Return an iterator over keys."""
        self._refresh()
        fuer key in self._toc:
            versuch:
                self._lookup(key)
            ausser KeyError:
                weiter
            liefere key

    def __contains__(self, key):
        """Return Wahr wenn the keyed message exists, Falsch otherwise."""
        self._refresh()
        gib key in self._toc

    def __len__(self):
        """Return a count of messages in the mailbox."""
        self._refresh()
        gib len(self._toc)

    def flush(self):
        """Write any pending changes to disk."""
        # Maildir changes are always written immediately, so there's nothing
        # to do.
        pass

    def lock(self):
        """Lock the mailbox."""
        gib

    def unlock(self):
        """Unlock the mailbox wenn it ist locked."""
        gib

    def close(self):
        """Flush und close the mailbox."""
        gib

    def list_folders(self):
        """Return a list of folder names."""
        result = []
        fuer entry in os.listdir(self._path):
            wenn len(entry) > 1 und entry[0] == '.' und \
               os.path.isdir(os.path.join(self._path, entry)):
                result.append(entry[1:])
        gib result

    def get_folder(self, folder):
        """Return a Maildir instance fuer the named folder."""
        gib Maildir(os.path.join(self._path, '.' + folder),
                       factory=self._factory,
                       create=Falsch)

    def add_folder(self, folder):
        """Create a folder und gib a Maildir instance representing it."""
        path = os.path.join(self._path, '.' + folder)
        result = Maildir(path, factory=self._factory)
        maildirfolder_path = os.path.join(path, 'maildirfolder')
        wenn nicht os.path.exists(maildirfolder_path):
            os.close(os.open(maildirfolder_path, os.O_CREAT | os.O_WRONLY,
                0o666))
        gib result

    def remove_folder(self, folder):
        """Delete the named folder, which must be empty."""
        path = os.path.join(self._path, '.' + folder)
        fuer entry in os.listdir(os.path.join(path, 'new')) + \
                     os.listdir(os.path.join(path, 'cur')):
            wenn len(entry) < 1 oder entry[0] != '.':
                wirf NotEmptyError('Folder contains message(s): %s' % folder)
        fuer entry in os.listdir(path):
            wenn entry != 'new' und entry != 'cur' und entry != 'tmp' und \
               os.path.isdir(os.path.join(path, entry)):
                wirf NotEmptyError("Folder contains subdirectory '%s': %s" %
                                    (folder, entry))
        fuer root, dirs, files in os.walk(path, topdown=Falsch):
            fuer entry in files:
                os.remove(os.path.join(root, entry))
            fuer entry in dirs:
                os.rmdir(os.path.join(root, entry))
        os.rmdir(path)

    def clean(self):
        """Delete old files in "tmp"."""
        now = time.time()
        fuer entry in os.listdir(os.path.join(self._path, 'tmp')):
            path = os.path.join(self._path, 'tmp', entry)
            wenn now - os.path.getatime(path) > 129600:   # 60 * 60 * 36
                os.remove(path)

    _count = 1  # This ist used to generate unique file names.

    def _create_tmp(self):
        """Create a file in the tmp subdirectory und open und gib it."""
        now = time.time()
        hostname = socket.gethostname()
        wenn '/' in hostname:
            hostname = hostname.replace('/', r'\057')
        wenn ':' in hostname:
            hostname = hostname.replace(':', r'\072')
        uniq = "%s.M%sP%sQ%s.%s" % (int(now), int(now % 1 * 1e6), os.getpid(),
                                    Maildir._count, hostname)
        path = os.path.join(self._path, 'tmp', uniq)
        versuch:
            os.stat(path)
        ausser FileNotFoundError:
            Maildir._count += 1
            versuch:
                gib _create_carefully(path)
            ausser FileExistsError:
                pass

        # Fall through to here wenn stat succeeded oder open raised EEXIST.
        wirf ExternalClashError('Name clash prevented file creation: %s' %
                                 path)

    def _refresh(self):
        """Update table of contents mapping."""
        # If it has been less than two seconds since the last _refresh() call,
        # we have to unconditionally re-read the mailbox just in case it has
        # been modified, because os.path.mtime() has a 2 sec resolution in the
        # most common worst case (FAT) und a 1 sec resolution typically.  This
        # results in a few unnecessary re-reads when _refresh() ist called
        # multiple times in that interval, but once the clock ticks over, we
        # will only re-read als needed.  Because the filesystem might be being
        # served by an independent system mit its own clock, we record und
        # compare mit the mtimes von the filesystem.  Because the other
        # system's clock might be skewing relative to our clock, we add an
        # extra delta to our wait.  The default ist one tenth second, but ist an
        # instance variable und so can be adjusted wenn dealing mit a
        # particularly skewed oder irregular system.
        wenn time.time() - self._last_read > 2 + self._skewfactor:
            refresh = Falsch
            fuer subdir in self._toc_mtimes:
                mtime = os.path.getmtime(self._paths[subdir])
                wenn mtime > self._toc_mtimes[subdir]:
                    refresh = Wahr
                self._toc_mtimes[subdir] = mtime
            wenn nicht refresh:
                gib
        # Refresh toc
        self._toc = {}
        fuer subdir in self._toc_mtimes:
            path = self._paths[subdir]
            fuer entry in os.listdir(path):
                wenn entry.startswith('.'):
                    weiter
                p = os.path.join(path, entry)
                wenn os.path.isdir(p):
                    weiter
                uniq = entry.split(self.colon)[0]
                self._toc[uniq] = os.path.join(subdir, entry)
        self._last_read = time.time()

    def _lookup(self, key):
        """Use TOC to gib subpath fuer given key, oder wirf a KeyError."""
        versuch:
            wenn os.path.exists(os.path.join(self._path, self._toc[key])):
                gib self._toc[key]
        ausser KeyError:
            pass
        self._refresh()
        versuch:
            gib self._toc[key]
        ausser KeyError:
            wirf KeyError('No message mit key: %s' % key) von Nichts

    # This method ist fuer backward compatibility only.
    def next(self):
        """Return the next message in a one-time iteration."""
        wenn nicht hasattr(self, '_onetime_keys'):
            self._onetime_keys = self.iterkeys()
        waehrend Wahr:
            versuch:
                gib self[next(self._onetime_keys)]
            ausser StopIteration:
                gib Nichts
            ausser KeyError:
                weiter


klasse _singlefileMailbox(Mailbox):
    """A single-file mailbox."""

    def __init__(self, path, factory=Nichts, create=Wahr):
        """Initialize a single-file mailbox."""
        Mailbox.__init__(self, path, factory, create)
        versuch:
            f = open(self._path, 'rb+')
        ausser OSError als e:
            wenn e.errno == errno.ENOENT:
                wenn create:
                    f = open(self._path, 'wb+')
                sonst:
                    wirf NoSuchMailboxError(self._path)
            sowenn e.errno in (errno.EACCES, errno.EROFS):
                f = open(self._path, 'rb')
            sonst:
                wirf
        self._file = f
        self._toc = Nichts
        self._next_key = 0
        self._pending = Falsch       # No changes require rewriting the file.
        self._pending_sync = Falsch  # No need to sync the file
        self._locked = Falsch
        self._file_length = Nichts    # Used to record mailbox size

    def add(self, message):
        """Add message und gib assigned key."""
        self._lookup()
        self._toc[self._next_key] = self._append_message(message)
        self._next_key += 1
        # _append_message appends the message to the mailbox file. We
        # don't need a full rewrite + rename, sync ist enough.
        self._pending_sync = Wahr
        gib self._next_key - 1

    def remove(self, key):
        """Remove the keyed message; wirf KeyError wenn it doesn't exist."""
        self._lookup(key)
        loesche self._toc[key]
        self._pending = Wahr

    def __setitem__(self, key, message):
        """Replace the keyed message; wirf KeyError wenn it doesn't exist."""
        self._lookup(key)
        self._toc[key] = self._append_message(message)
        self._pending = Wahr

    def iterkeys(self):
        """Return an iterator over keys."""
        self._lookup()
        liefere von self._toc.keys()

    def __contains__(self, key):
        """Return Wahr wenn the keyed message exists, Falsch otherwise."""
        self._lookup()
        gib key in self._toc

    def __len__(self):
        """Return a count of messages in the mailbox."""
        self._lookup()
        gib len(self._toc)

    def lock(self):
        """Lock the mailbox."""
        wenn nicht self._locked:
            _lock_file(self._file)
            self._locked = Wahr

    def unlock(self):
        """Unlock the mailbox wenn it ist locked."""
        wenn self._locked:
            _unlock_file(self._file)
            self._locked = Falsch

    def flush(self):
        """Write any pending changes to disk."""
        wenn nicht self._pending:
            wenn self._pending_sync:
                # Messages have only been added, so syncing the file
                # ist enough.
                _sync_flush(self._file)
                self._pending_sync = Falsch
            gib

        # In order to be writing anything out at all, self._toc must
        # already have been generated (and presumably has been modified
        # by adding oder deleting an item).
        assert self._toc ist nicht Nichts

        # Check length of self._file; wenn it's changed, some other process
        # has modified the mailbox since we scanned it.
        self._file.seek(0, 2)
        cur_len = self._file.tell()
        wenn cur_len != self._file_length:
            wirf ExternalClashError('Size of mailbox file changed '
                                     '(expected %i, found %i)' %
                                     (self._file_length, cur_len))

        new_file = _create_temporary(self._path)
        versuch:
            new_toc = {}
            self._pre_mailbox_hook(new_file)
            fuer key in sorted(self._toc.keys()):
                start, stop = self._toc[key]
                self._file.seek(start)
                self._pre_message_hook(new_file)
                new_start = new_file.tell()
                waehrend Wahr:
                    buffer = self._file.read(min(4096,
                                                 stop - self._file.tell()))
                    wenn nicht buffer:
                        breche
                    new_file.write(buffer)
                new_toc[key] = (new_start, new_file.tell())
                self._post_message_hook(new_file)
            self._file_length = new_file.tell()
        ausser:
            new_file.close()
            os.remove(new_file.name)
            wirf
        _sync_close(new_file)
        # self._file ist about to get replaced, so no need to sync.
        self._file.close()
        # Make sure the new file's mode und owner are the same als the old file's
        info = os.stat(self._path)
        os.chmod(new_file.name, info.st_mode)
        versuch:
            os.chown(new_file.name, info.st_uid, info.st_gid)
        ausser (AttributeError, OSError):
            pass
        versuch:
            os.rename(new_file.name, self._path)
        ausser FileExistsError:
            os.remove(self._path)
            os.rename(new_file.name, self._path)
        self._file = open(self._path, 'rb+')
        self._toc = new_toc
        self._pending = Falsch
        self._pending_sync = Falsch
        wenn self._locked:
            _lock_file(self._file, dotlock=Falsch)

    def _pre_mailbox_hook(self, f):
        """Called before writing the mailbox to file f."""
        gib

    def _pre_message_hook(self, f):
        """Called before writing each message to file f."""
        gib

    def _post_message_hook(self, f):
        """Called after writing each message to file f."""
        gib

    def close(self):
        """Flush und close the mailbox."""
        versuch:
            self.flush()
        schliesslich:
            versuch:
                wenn self._locked:
                    self.unlock()
            schliesslich:
                self._file.close()  # Sync has been done by self.flush() above.

    def _lookup(self, key=Nichts):
        """Return (start, stop) oder wirf KeyError."""
        wenn self._toc ist Nichts:
            self._generate_toc()
        wenn key ist nicht Nichts:
            versuch:
                gib self._toc[key]
            ausser KeyError:
                wirf KeyError('No message mit key: %s' % key) von Nichts

    def _append_message(self, message):
        """Append message to mailbox und gib (start, stop) offsets."""
        self._file.seek(0, 2)
        before = self._file.tell()
        wenn len(self._toc) == 0 und nicht self._pending:
            # This ist the first message, und the _pre_mailbox_hook
            # hasn't yet been called. If self._pending ist Wahr,
            # messages have been removed, so _pre_mailbox_hook must
            # have been called already.
            self._pre_mailbox_hook(self._file)
        versuch:
            self._pre_message_hook(self._file)
            offsets = self._install_message(message)
            self._post_message_hook(self._file)
        ausser BaseException:
            self._file.truncate(before)
            wirf
        self._file.flush()
        self._file_length = self._file.tell()  # Record current length of mailbox
        gib offsets



klasse _mboxMMDF(_singlefileMailbox):
    """An mbox oder MMDF mailbox."""

    _mangle_from_ = Wahr

    def get_message(self, key):
        """Return a Message representation oder wirf a KeyError."""
        start, stop = self._lookup(key)
        self._file.seek(start)
        from_line = self._file.readline().replace(linesep, b'').decode('ascii')
        string = self._file.read(stop - self._file.tell())
        msg = self._message_factory(string.replace(linesep, b'\n'))
        msg.set_unixfrom(from_line)
        msg.set_from(from_line[5:])
        gib msg

    def get_string(self, key, from_=Falsch):
        """Return a string representation oder wirf a KeyError."""
        gib email.message_from_bytes(
            self.get_bytes(key, from_)).as_string(unixfrom=from_)

    def get_bytes(self, key, from_=Falsch):
        """Return a string representation oder wirf a KeyError."""
        start, stop = self._lookup(key)
        self._file.seek(start)
        wenn nicht from_:
            self._file.readline()
        string = self._file.read(stop - self._file.tell())
        gib string.replace(linesep, b'\n')

    def get_file(self, key, from_=Falsch):
        """Return a file-like representation oder wirf a KeyError."""
        start, stop = self._lookup(key)
        self._file.seek(start)
        wenn nicht from_:
            self._file.readline()
        gib _PartialFile(self._file, self._file.tell(), stop)

    def _install_message(self, message):
        """Format a message und blindly write to self._file."""
        from_line = Nichts
        wenn isinstance(message, str):
            message = self._string_to_bytes(message)
        wenn isinstance(message, bytes) und message.startswith(b'From '):
            newline = message.find(b'\n')
            wenn newline != -1:
                from_line = message[:newline]
                message = message[newline + 1:]
            sonst:
                from_line = message
                message = b''
        sowenn isinstance(message, _mboxMMDFMessage):
            author = message.get_from().encode('ascii')
            from_line = b'From ' + author
        sowenn isinstance(message, email.message.Message):
            from_line = message.get_unixfrom()  # May be Nichts.
            wenn from_line ist nicht Nichts:
                from_line = from_line.encode('ascii')
        wenn from_line ist Nichts:
            from_line = b'From MAILER-DAEMON ' + time.asctime(time.gmtime()).encode()
        start = self._file.tell()
        self._file.write(from_line + linesep)
        self._dump_message(message, self._file, self._mangle_from_)
        stop = self._file.tell()
        gib (start, stop)


klasse mbox(_mboxMMDF):
    """A classic mbox mailbox."""

    _mangle_from_ = Wahr

    # All messages must end in a newline character, und
    # _post_message_hooks outputs an empty line between messages.
    _append_newline = Wahr

    def __init__(self, path, factory=Nichts, create=Wahr):
        """Initialize an mbox mailbox."""
        self._message_factory = mboxMessage
        _mboxMMDF.__init__(self, path, factory, create)

    def _post_message_hook(self, f):
        """Called after writing each message to file f."""
        f.write(linesep)

    def _generate_toc(self):
        """Generate key-to-(start, stop) table of contents."""
        starts, stops = [], []
        last_was_empty = Falsch
        self._file.seek(0)
        waehrend Wahr:
            line_pos = self._file.tell()
            line = self._file.readline()
            wenn line.startswith(b'From '):
                wenn len(stops) < len(starts):
                    wenn last_was_empty:
                        stops.append(line_pos - len(linesep))
                    sonst:
                        # The last line before the "From " line wasn't
                        # blank, but we consider it a start of a
                        # message anyway.
                        stops.append(line_pos)
                starts.append(line_pos)
                last_was_empty = Falsch
            sowenn nicht line:
                wenn last_was_empty:
                    stops.append(line_pos - len(linesep))
                sonst:
                    stops.append(line_pos)
                breche
            sowenn line == linesep:
                last_was_empty = Wahr
            sonst:
                last_was_empty = Falsch
        self._toc = dict(enumerate(zip(starts, stops)))
        self._next_key = len(self._toc)
        self._file_length = self._file.tell()


klasse MMDF(_mboxMMDF):
    """An MMDF mailbox."""

    def __init__(self, path, factory=Nichts, create=Wahr):
        """Initialize an MMDF mailbox."""
        self._message_factory = MMDFMessage
        _mboxMMDF.__init__(self, path, factory, create)

    def _pre_message_hook(self, f):
        """Called before writing each message to file f."""
        f.write(b'\001\001\001\001' + linesep)

    def _post_message_hook(self, f):
        """Called after writing each message to file f."""
        f.write(linesep + b'\001\001\001\001' + linesep)

    def _generate_toc(self):
        """Generate key-to-(start, stop) table of contents."""
        starts, stops = [], []
        self._file.seek(0)
        next_pos = 0
        waehrend Wahr:
            line_pos = next_pos
            line = self._file.readline()
            next_pos = self._file.tell()
            wenn line.startswith(b'\001\001\001\001' + linesep):
                starts.append(next_pos)
                waehrend Wahr:
                    line_pos = next_pos
                    line = self._file.readline()
                    next_pos = self._file.tell()
                    wenn line == b'\001\001\001\001' + linesep:
                        stops.append(line_pos - len(linesep))
                        breche
                    sowenn nicht line:
                        stops.append(line_pos)
                        breche
            sowenn nicht line:
                breche
        self._toc = dict(enumerate(zip(starts, stops)))
        self._next_key = len(self._toc)
        self._file.seek(0, 2)
        self._file_length = self._file.tell()


klasse MH(Mailbox):
    """An MH mailbox."""

    def __init__(self, path, factory=Nichts, create=Wahr):
        """Initialize an MH instance."""
        Mailbox.__init__(self, path, factory, create)
        wenn nicht os.path.exists(self._path):
            wenn create:
                os.mkdir(self._path, 0o700)
                os.close(os.open(os.path.join(self._path, '.mh_sequences'),
                                 os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
            sonst:
                wirf NoSuchMailboxError(self._path)
        self._locked = Falsch

    def add(self, message):
        """Add message und gib assigned key."""
        keys = self.keys()
        wenn len(keys) == 0:
            new_key = 1
        sonst:
            new_key = max(keys) + 1
        new_path = os.path.join(self._path, str(new_key))
        f = _create_carefully(new_path)
        closed = Falsch
        versuch:
            wenn self._locked:
                _lock_file(f)
            versuch:
                versuch:
                    self._dump_message(message, f)
                ausser BaseException:
                    # Unlock und close so it can be deleted on Windows
                    wenn self._locked:
                        _unlock_file(f)
                    _sync_close(f)
                    closed = Wahr
                    os.remove(new_path)
                    wirf
                wenn isinstance(message, MHMessage):
                    self._dump_sequences(message, new_key)
            schliesslich:
                wenn self._locked:
                    _unlock_file(f)
        schliesslich:
            wenn nicht closed:
                _sync_close(f)
        gib new_key

    def remove(self, key):
        """Remove the keyed message; wirf KeyError wenn it doesn't exist."""
        path = os.path.join(self._path, str(key))
        versuch:
            f = open(path, 'rb+')
        ausser OSError als e:
            wenn e.errno == errno.ENOENT:
                wirf KeyError('No message mit key: %s' % key)
            sonst:
                wirf
        sonst:
            f.close()
            os.remove(path)

    def __setitem__(self, key, message):
        """Replace the keyed message; wirf KeyError wenn it doesn't exist."""
        path = os.path.join(self._path, str(key))
        versuch:
            f = open(path, 'rb+')
        ausser OSError als e:
            wenn e.errno == errno.ENOENT:
                wirf KeyError('No message mit key: %s' % key)
            sonst:
                wirf
        versuch:
            wenn self._locked:
                _lock_file(f)
            versuch:
                os.close(os.open(path, os.O_WRONLY | os.O_TRUNC))
                self._dump_message(message, f)
                wenn isinstance(message, MHMessage):
                    self._dump_sequences(message, key)
            schliesslich:
                wenn self._locked:
                    _unlock_file(f)
        schliesslich:
            _sync_close(f)

    def get_message(self, key):
        """Return a Message representation oder wirf a KeyError."""
        versuch:
            wenn self._locked:
                f = open(os.path.join(self._path, str(key)), 'rb+')
            sonst:
                f = open(os.path.join(self._path, str(key)), 'rb')
        ausser OSError als e:
            wenn e.errno == errno.ENOENT:
                wirf KeyError('No message mit key: %s' % key)
            sonst:
                wirf
        mit f:
            wenn self._locked:
                _lock_file(f)
            versuch:
                msg = MHMessage(f)
            schliesslich:
                wenn self._locked:
                    _unlock_file(f)
        fuer name, key_list in self.get_sequences().items():
            wenn key in key_list:
                msg.add_sequence(name)
        gib msg

    def get_bytes(self, key):
        """Return a bytes representation oder wirf a KeyError."""
        versuch:
            wenn self._locked:
                f = open(os.path.join(self._path, str(key)), 'rb+')
            sonst:
                f = open(os.path.join(self._path, str(key)), 'rb')
        ausser OSError als e:
            wenn e.errno == errno.ENOENT:
                wirf KeyError('No message mit key: %s' % key)
            sonst:
                wirf
        mit f:
            wenn self._locked:
                _lock_file(f)
            versuch:
                gib f.read().replace(linesep, b'\n')
            schliesslich:
                wenn self._locked:
                    _unlock_file(f)

    def get_file(self, key):
        """Return a file-like representation oder wirf a KeyError."""
        versuch:
            f = open(os.path.join(self._path, str(key)), 'rb')
        ausser OSError als e:
            wenn e.errno == errno.ENOENT:
                wirf KeyError('No message mit key: %s' % key)
            sonst:
                wirf
        gib _ProxyFile(f)

    def iterkeys(self):
        """Return an iterator over keys."""
        gib iter(sorted(int(entry) fuer entry in os.listdir(self._path)
                                      wenn entry.isdigit()))

    def __contains__(self, key):
        """Return Wahr wenn the keyed message exists, Falsch otherwise."""
        gib os.path.exists(os.path.join(self._path, str(key)))

    def __len__(self):
        """Return a count of messages in the mailbox."""
        gib len(list(self.iterkeys()))

    def _open_mh_sequences_file(self, text):
        mode = '' wenn text sonst 'b'
        kwargs = {'encoding': 'ASCII'} wenn text sonst {}
        path = os.path.join(self._path, '.mh_sequences')
        waehrend Wahr:
            versuch:
                gib open(path, 'r+' + mode, **kwargs)
            ausser FileNotFoundError:
                pass
            versuch:
                gib open(path, 'x+' + mode, **kwargs)
            ausser FileExistsError:
                pass

    def lock(self):
        """Lock the mailbox."""
        wenn nicht self._locked:
            self._file = self._open_mh_sequences_file(text=Falsch)
            _lock_file(self._file)
            self._locked = Wahr

    def unlock(self):
        """Unlock the mailbox wenn it ist locked."""
        wenn self._locked:
            _unlock_file(self._file)
            _sync_close(self._file)
            loesche self._file
            self._locked = Falsch

    def flush(self):
        """Write any pending changes to the disk."""
        gib

    def close(self):
        """Flush und close the mailbox."""
        wenn self._locked:
            self.unlock()

    def list_folders(self):
        """Return a list of folder names."""
        result = []
        fuer entry in os.listdir(self._path):
            wenn os.path.isdir(os.path.join(self._path, entry)):
                result.append(entry)
        gib result

    def get_folder(self, folder):
        """Return an MH instance fuer the named folder."""
        gib MH(os.path.join(self._path, folder),
                  factory=self._factory, create=Falsch)

    def add_folder(self, folder):
        """Create a folder und gib an MH instance representing it."""
        gib MH(os.path.join(self._path, folder),
                  factory=self._factory)

    def remove_folder(self, folder):
        """Delete the named folder, which must be empty."""
        path = os.path.join(self._path, folder)
        entries = os.listdir(path)
        wenn entries == ['.mh_sequences']:
            os.remove(os.path.join(path, '.mh_sequences'))
        sowenn entries == []:
            pass
        sonst:
            wirf NotEmptyError('Folder nicht empty: %s' % self._path)
        os.rmdir(path)

    def get_sequences(self):
        """Return a name-to-key-list dictionary to define each sequence."""
        results = {}
        versuch:
            f = open(os.path.join(self._path, '.mh_sequences'), 'r', encoding='ASCII')
        ausser FileNotFoundError:
            gib results
        mit f:
            all_keys = set(self.keys())
            fuer line in f:
                versuch:
                    name, contents = line.split(':')
                    keys = set()
                    fuer spec in contents.split():
                        wenn spec.isdigit():
                            keys.add(int(spec))
                        sonst:
                            start, stop = (int(x) fuer x in spec.split('-'))
                            keys.update(range(start, stop + 1))
                    results[name] = [key fuer key in sorted(keys) \
                                         wenn key in all_keys]
                    wenn len(results[name]) == 0:
                        loesche results[name]
                ausser ValueError:
                    wirf FormatError('Invalid sequence specification: %s' %
                                      line.rstrip())
        gib results

    def set_sequences(self, sequences):
        """Set sequences using the given name-to-key-list dictionary."""
        f = self._open_mh_sequences_file(text=Wahr)
        versuch:
            os.close(os.open(f.name, os.O_WRONLY | os.O_TRUNC))
            fuer name, keys in sequences.items():
                wenn len(keys) == 0:
                    weiter
                f.write(name + ':')
                prev = Nichts
                completing = Falsch
                fuer key in sorted(set(keys)):
                    wenn key - 1 == prev:
                        wenn nicht completing:
                            completing = Wahr
                            f.write('-')
                    sowenn completing:
                        completing = Falsch
                        f.write('%s %s' % (prev, key))
                    sonst:
                        f.write(' %s' % key)
                    prev = key
                wenn completing:
                    f.write(str(prev) + '\n')
                sonst:
                    f.write('\n')
        schliesslich:
            _sync_close(f)

    def pack(self):
        """Re-name messages to eliminate numbering gaps. Invalidates keys."""
        sequences = self.get_sequences()
        prev = 0
        changes = []
        fuer key in self.iterkeys():
            wenn key - 1 != prev:
                changes.append((key, prev + 1))
                versuch:
                    os.link(os.path.join(self._path, str(key)),
                            os.path.join(self._path, str(prev + 1)))
                ausser (AttributeError, PermissionError):
                    os.rename(os.path.join(self._path, str(key)),
                              os.path.join(self._path, str(prev + 1)))
                sonst:
                    os.unlink(os.path.join(self._path, str(key)))
            prev += 1
        self._next_key = prev + 1
        wenn len(changes) == 0:
            gib
        fuer name, key_list in sequences.items():
            fuer old, new in changes:
                wenn old in key_list:
                    key_list[key_list.index(old)] = new
        self.set_sequences(sequences)

    def _dump_sequences(self, message, key):
        """Inspect a new MHMessage und update sequences appropriately."""
        pending_sequences = message.get_sequences()
        all_sequences = self.get_sequences()
        fuer name, key_list in all_sequences.items():
            wenn name in pending_sequences:
                key_list.append(key)
            sowenn key in key_list:
                loesche key_list[key_list.index(key)]
        fuer sequence in pending_sequences:
            wenn sequence nicht in all_sequences:
                all_sequences[sequence] = [key]
        self.set_sequences(all_sequences)


klasse Babyl(_singlefileMailbox):
    """An Rmail-style Babyl mailbox."""

    _special_labels = frozenset({'unseen', 'deleted', 'filed', 'answered',
                                 'forwarded', 'edited', 'resent'})

    def __init__(self, path, factory=Nichts, create=Wahr):
        """Initialize a Babyl mailbox."""
        _singlefileMailbox.__init__(self, path, factory, create)
        self._labels = {}

    def add(self, message):
        """Add message und gib assigned key."""
        key = _singlefileMailbox.add(self, message)
        wenn isinstance(message, BabylMessage):
            self._labels[key] = message.get_labels()
        gib key

    def remove(self, key):
        """Remove the keyed message; wirf KeyError wenn it doesn't exist."""
        _singlefileMailbox.remove(self, key)
        wenn key in self._labels:
            loesche self._labels[key]

    def __setitem__(self, key, message):
        """Replace the keyed message; wirf KeyError wenn it doesn't exist."""
        _singlefileMailbox.__setitem__(self, key, message)
        wenn isinstance(message, BabylMessage):
            self._labels[key] = message.get_labels()

    def get_message(self, key):
        """Return a Message representation oder wirf a KeyError."""
        start, stop = self._lookup(key)
        self._file.seek(start)
        self._file.readline()   # Skip b'1,' line specifying labels.
        original_headers = io.BytesIO()
        waehrend Wahr:
            line = self._file.readline()
            wenn line == b'*** EOOH ***' + linesep oder nicht line:
                breche
            original_headers.write(line.replace(linesep, b'\n'))
        visible_headers = io.BytesIO()
        waehrend Wahr:
            line = self._file.readline()
            wenn line == linesep oder nicht line:
                breche
            visible_headers.write(line.replace(linesep, b'\n'))
        # Read up to the stop, oder to the end
        n = stop - self._file.tell()
        assert n >= 0
        body = self._file.read(n)
        body = body.replace(linesep, b'\n')
        msg = BabylMessage(original_headers.getvalue() + body)
        msg.set_visible(visible_headers.getvalue())
        wenn key in self._labels:
            msg.set_labels(self._labels[key])
        gib msg

    def get_bytes(self, key):
        """Return a string representation oder wirf a KeyError."""
        start, stop = self._lookup(key)
        self._file.seek(start)
        self._file.readline()   # Skip b'1,' line specifying labels.
        original_headers = io.BytesIO()
        waehrend Wahr:
            line = self._file.readline()
            wenn line == b'*** EOOH ***' + linesep oder nicht line:
                breche
            original_headers.write(line.replace(linesep, b'\n'))
        waehrend Wahr:
            line = self._file.readline()
            wenn line == linesep oder nicht line:
                breche
        headers = original_headers.getvalue()
        n = stop - self._file.tell()
        assert n >= 0
        data = self._file.read(n)
        data = data.replace(linesep, b'\n')
        gib headers + data

    def get_file(self, key):
        """Return a file-like representation oder wirf a KeyError."""
        gib io.BytesIO(self.get_bytes(key).replace(b'\n', linesep))

    def get_labels(self):
        """Return a list of user-defined labels in the mailbox."""
        self._lookup()
        labels = set()
        fuer label_list in self._labels.values():
            labels.update(label_list)
        labels.difference_update(self._special_labels)
        gib list(labels)

    def _generate_toc(self):
        """Generate key-to-(start, stop) table of contents."""
        starts, stops = [], []
        self._file.seek(0)
        next_pos = 0
        label_lists = []
        waehrend Wahr:
            line_pos = next_pos
            line = self._file.readline()
            next_pos = self._file.tell()
            wenn line == b'\037\014' + linesep:
                wenn len(stops) < len(starts):
                    stops.append(line_pos - len(linesep))
                starts.append(next_pos)
                labels = [label.strip() fuer label
                                        in self._file.readline()[1:].split(b',')
                                        wenn label.strip()]
                label_lists.append(labels)
            sowenn line == b'\037' oder line == b'\037' + linesep:
                wenn len(stops) < len(starts):
                    stops.append(line_pos - len(linesep))
            sowenn nicht line:
                stops.append(line_pos - len(linesep))
                breche
        self._toc = dict(enumerate(zip(starts, stops)))
        self._labels = dict(enumerate(label_lists))
        self._next_key = len(self._toc)
        self._file.seek(0, 2)
        self._file_length = self._file.tell()

    def _pre_mailbox_hook(self, f):
        """Called before writing the mailbox to file f."""
        babyl = b'BABYL OPTIONS:' + linesep
        babyl += b'Version: 5' + linesep
        labels = self.get_labels()
        labels = (label.encode() fuer label in labels)
        babyl += b'Labels:' + b','.join(labels) + linesep
        babyl += b'\037'
        f.write(babyl)

    def _pre_message_hook(self, f):
        """Called before writing each message to file f."""
        f.write(b'\014' + linesep)

    def _post_message_hook(self, f):
        """Called after writing each message to file f."""
        f.write(linesep + b'\037')

    def _install_message(self, message):
        """Write message contents und gib (start, stop)."""
        start = self._file.tell()
        wenn isinstance(message, BabylMessage):
            special_labels = []
            labels = []
            fuer label in message.get_labels():
                wenn label in self._special_labels:
                    special_labels.append(label)
                sonst:
                    labels.append(label)
            self._file.write(b'1')
            fuer label in special_labels:
                self._file.write(b', ' + label.encode())
            self._file.write(b',,')
            fuer label in labels:
                self._file.write(b' ' + label.encode() + b',')
            self._file.write(linesep)
        sonst:
            self._file.write(b'1,,' + linesep)
        wenn isinstance(message, email.message.Message):
            orig_buffer = io.BytesIO()
            orig_generator = email.generator.BytesGenerator(orig_buffer, Falsch, 0)
            orig_generator.flatten(message)
            orig_buffer.seek(0)
            waehrend Wahr:
                line = orig_buffer.readline()
                self._file.write(line.replace(b'\n', linesep))
                wenn line == b'\n' oder nicht line:
                    breche
            self._file.write(b'*** EOOH ***' + linesep)
            wenn isinstance(message, BabylMessage):
                vis_buffer = io.BytesIO()
                vis_generator = email.generator.BytesGenerator(vis_buffer, Falsch, 0)
                vis_generator.flatten(message.get_visible())
                waehrend Wahr:
                    line = vis_buffer.readline()
                    self._file.write(line.replace(b'\n', linesep))
                    wenn line == b'\n' oder nicht line:
                        breche
            sonst:
                orig_buffer.seek(0)
                waehrend Wahr:
                    line = orig_buffer.readline()
                    self._file.write(line.replace(b'\n', linesep))
                    wenn line == b'\n' oder nicht line:
                        breche
            waehrend Wahr:
                buffer = orig_buffer.read(4096) # Buffer size ist arbitrary.
                wenn nicht buffer:
                    breche
                self._file.write(buffer.replace(b'\n', linesep))
        sowenn isinstance(message, (bytes, str, io.StringIO)):
            wenn isinstance(message, io.StringIO):
                warnings.warn("Use of StringIO input ist deprecated, "
                    "use BytesIO instead", DeprecationWarning, 3)
                message = message.getvalue()
            wenn isinstance(message, str):
                message = self._string_to_bytes(message)
            body_start = message.find(b'\n\n') + 2
            wenn body_start - 2 != -1:
                self._file.write(message[:body_start].replace(b'\n', linesep))
                self._file.write(b'*** EOOH ***' + linesep)
                self._file.write(message[:body_start].replace(b'\n', linesep))
                self._file.write(message[body_start:].replace(b'\n', linesep))
            sonst:
                self._file.write(b'*** EOOH ***' + linesep + linesep)
                self._file.write(message.replace(b'\n', linesep))
        sowenn hasattr(message, 'readline'):
            wenn hasattr(message, 'buffer'):
                warnings.warn("Use of text mode files ist deprecated, "
                    "use a binary mode file instead", DeprecationWarning, 3)
                message = message.buffer
            original_pos = message.tell()
            first_pass = Wahr
            waehrend Wahr:
                line = message.readline()
                # Universal newline support.
                wenn line.endswith(b'\r\n'):
                    line = line[:-2] + b'\n'
                sowenn line.endswith(b'\r'):
                    line = line[:-1] + b'\n'
                self._file.write(line.replace(b'\n', linesep))
                wenn line == b'\n' oder nicht line:
                    wenn first_pass:
                        first_pass = Falsch
                        self._file.write(b'*** EOOH ***' + linesep)
                        message.seek(original_pos)
                    sonst:
                        breche
            waehrend Wahr:
                line = message.readline()
                wenn nicht line:
                    breche
                # Universal newline support.
                wenn line.endswith(b'\r\n'):
                    line = line[:-2] + linesep
                sowenn line.endswith(b'\r'):
                    line = line[:-1] + linesep
                sowenn line.endswith(b'\n'):
                    line = line[:-1] + linesep
                self._file.write(line)
        sonst:
            wirf TypeError('Invalid message type: %s' % type(message))
        stop = self._file.tell()
        gib (start, stop)


klasse Message(email.message.Message):
    """Message mit mailbox-format-specific properties."""

    def __init__(self, message=Nichts):
        """Initialize a Message instance."""
        wenn isinstance(message, email.message.Message):
            self._become_message(copy.deepcopy(message))
            wenn isinstance(message, Message):
                message._explain_to(self)
        sowenn isinstance(message, bytes):
            self._become_message(email.message_from_bytes(message))
        sowenn isinstance(message, str):
            self._become_message(email.message_from_string(message))
        sowenn isinstance(message, io.TextIOWrapper):
            self._become_message(email.message_from_file(message))
        sowenn hasattr(message, "read"):
            self._become_message(email.message_from_binary_file(message))
        sowenn message ist Nichts:
            email.message.Message.__init__(self)
        sonst:
            wirf TypeError('Invalid message type: %s' % type(message))

    def _become_message(self, message):
        """Assume the non-format-specific state of message."""
        type_specific = getattr(message, '_type_specific_attributes', [])
        fuer name in message.__dict__:
            wenn name nicht in type_specific:
                self.__dict__[name] = message.__dict__[name]

    def _explain_to(self, message):
        """Copy format-specific state to message insofar als possible."""
        wenn isinstance(message, Message):
            gib  # There's nothing format-specific to explain.
        sonst:
            wirf TypeError('Cannot convert to specified type')


klasse MaildirMessage(Message):
    """Message mit Maildir-specific properties."""

    _type_specific_attributes = ['_subdir', '_info', '_date']

    def __init__(self, message=Nichts):
        """Initialize a MaildirMessage instance."""
        self._subdir = 'new'
        self._info = ''
        self._date = time.time()
        Message.__init__(self, message)

    def get_subdir(self):
        """Return 'new' oder 'cur'."""
        gib self._subdir

    def set_subdir(self, subdir):
        """Set subdir to 'new' oder 'cur'."""
        wenn subdir == 'new' oder subdir == 'cur':
            self._subdir = subdir
        sonst:
            wirf ValueError("subdir must be 'new' oder 'cur': %s" % subdir)

    def get_flags(self):
        """Return als a string the flags that are set."""
        wenn self._info.startswith('2,'):
            gib self._info[2:]
        sonst:
            gib ''

    def set_flags(self, flags):
        """Set the given flags und unset all others."""
        self._info = '2,' + ''.join(sorted(flags))

    def add_flag(self, flag):
        """Set the given flag(s) without changing others."""
        self.set_flags(''.join(set(self.get_flags()) | set(flag)))

    def remove_flag(self, flag):
        """Unset the given string flag(s) without changing others."""
        wenn self.get_flags():
            self.set_flags(''.join(set(self.get_flags()) - set(flag)))

    def get_date(self):
        """Return delivery date of message, in seconds since the epoch."""
        gib self._date

    def set_date(self, date):
        """Set delivery date of message, in seconds since the epoch."""
        versuch:
            self._date = float(date)
        ausser ValueError:
            wirf TypeError("can't convert to float: %s" % date) von Nichts

    def get_info(self):
        """Get the message's "info" als a string."""
        gib self._info

    def set_info(self, info):
        """Set the message's "info" string."""
        wenn isinstance(info, str):
            self._info = info
        sonst:
            wirf TypeError('info must be a string: %s' % type(info))

    def _explain_to(self, message):
        """Copy Maildir-specific state to message insofar als possible."""
        wenn isinstance(message, MaildirMessage):
            message.set_flags(self.get_flags())
            message.set_subdir(self.get_subdir())
            message.set_date(self.get_date())
        sowenn isinstance(message, _mboxMMDFMessage):
            flags = set(self.get_flags())
            wenn 'S' in flags:
                message.add_flag('R')
            wenn self.get_subdir() == 'cur':
                message.add_flag('O')
            wenn 'T' in flags:
                message.add_flag('D')
            wenn 'F' in flags:
                message.add_flag('F')
            wenn 'R' in flags:
                message.add_flag('A')
            message.set_from('MAILER-DAEMON', time.gmtime(self.get_date()))
        sowenn isinstance(message, MHMessage):
            flags = set(self.get_flags())
            wenn 'S' nicht in flags:
                message.add_sequence('unseen')
            wenn 'R' in flags:
                message.add_sequence('replied')
            wenn 'F' in flags:
                message.add_sequence('flagged')
        sowenn isinstance(message, BabylMessage):
            flags = set(self.get_flags())
            wenn 'S' nicht in flags:
                message.add_label('unseen')
            wenn 'T' in flags:
                message.add_label('deleted')
            wenn 'R' in flags:
                message.add_label('answered')
            wenn 'P' in flags:
                message.add_label('forwarded')
        sowenn isinstance(message, Message):
            pass
        sonst:
            wirf TypeError('Cannot convert to specified type: %s' %
                            type(message))


klasse _mboxMMDFMessage(Message):
    """Message mit mbox- oder MMDF-specific properties."""

    _type_specific_attributes = ['_from']

    def __init__(self, message=Nichts):
        """Initialize an mboxMMDFMessage instance."""
        self.set_from('MAILER-DAEMON', Wahr)
        wenn isinstance(message, email.message.Message):
            unixfrom = message.get_unixfrom()
            wenn unixfrom ist nicht Nichts und unixfrom.startswith('From '):
                self.set_from(unixfrom[5:])
        Message.__init__(self, message)

    def get_from(self):
        """Return contents of "From " line."""
        gib self._from

    def set_from(self, from_, time_=Nichts):
        """Set "From " line, formatting und appending time_ wenn specified."""
        wenn time_ ist nicht Nichts:
            wenn time_ ist Wahr:
                time_ = time.gmtime()
            from_ += ' ' + time.asctime(time_)
        self._from = from_

    def get_flags(self):
        """Return als a string the flags that are set."""
        gib self.get('Status', '') + self.get('X-Status', '')

    def set_flags(self, flags):
        """Set the given flags und unset all others."""
        flags = set(flags)
        status_flags, xstatus_flags = '', ''
        fuer flag in ('R', 'O'):
            wenn flag in flags:
                status_flags += flag
                flags.remove(flag)
        fuer flag in ('D', 'F', 'A'):
            wenn flag in flags:
                xstatus_flags += flag
                flags.remove(flag)
        xstatus_flags += ''.join(sorted(flags))
        versuch:
            self.replace_header('Status', status_flags)
        ausser KeyError:
            self.add_header('Status', status_flags)
        versuch:
            self.replace_header('X-Status', xstatus_flags)
        ausser KeyError:
            self.add_header('X-Status', xstatus_flags)

    def add_flag(self, flag):
        """Set the given flag(s) without changing others."""
        self.set_flags(''.join(set(self.get_flags()) | set(flag)))

    def remove_flag(self, flag):
        """Unset the given string flag(s) without changing others."""
        wenn 'Status' in self oder 'X-Status' in self:
            self.set_flags(''.join(set(self.get_flags()) - set(flag)))

    def _explain_to(self, message):
        """Copy mbox- oder MMDF-specific state to message insofar als possible."""
        wenn isinstance(message, MaildirMessage):
            flags = set(self.get_flags())
            wenn 'O' in flags:
                message.set_subdir('cur')
            wenn 'F' in flags:
                message.add_flag('F')
            wenn 'A' in flags:
                message.add_flag('R')
            wenn 'R' in flags:
                message.add_flag('S')
            wenn 'D' in flags:
                message.add_flag('T')
            loesche message['status']
            loesche message['x-status']
            maybe_date = ' '.join(self.get_from().split()[-5:])
            versuch:
                message.set_date(calendar.timegm(time.strptime(maybe_date,
                                                      '%a %b %d %H:%M:%S %Y')))
            ausser (ValueError, OverflowError):
                pass
        sowenn isinstance(message, _mboxMMDFMessage):
            message.set_flags(self.get_flags())
            message.set_from(self.get_from())
        sowenn isinstance(message, MHMessage):
            flags = set(self.get_flags())
            wenn 'R' nicht in flags:
                message.add_sequence('unseen')
            wenn 'A' in flags:
                message.add_sequence('replied')
            wenn 'F' in flags:
                message.add_sequence('flagged')
            loesche message['status']
            loesche message['x-status']
        sowenn isinstance(message, BabylMessage):
            flags = set(self.get_flags())
            wenn 'R' nicht in flags:
                message.add_label('unseen')
            wenn 'D' in flags:
                message.add_label('deleted')
            wenn 'A' in flags:
                message.add_label('answered')
            loesche message['status']
            loesche message['x-status']
        sowenn isinstance(message, Message):
            pass
        sonst:
            wirf TypeError('Cannot convert to specified type: %s' %
                            type(message))


klasse mboxMessage(_mboxMMDFMessage):
    """Message mit mbox-specific properties."""


klasse MHMessage(Message):
    """Message mit MH-specific properties."""

    _type_specific_attributes = ['_sequences']

    def __init__(self, message=Nichts):
        """Initialize an MHMessage instance."""
        self._sequences = []
        Message.__init__(self, message)

    def get_sequences(self):
        """Return a list of sequences that include the message."""
        gib self._sequences[:]

    def set_sequences(self, sequences):
        """Set the list of sequences that include the message."""
        self._sequences = list(sequences)

    def add_sequence(self, sequence):
        """Add sequence to list of sequences including the message."""
        wenn isinstance(sequence, str):
            wenn nicht sequence in self._sequences:
                self._sequences.append(sequence)
        sonst:
            wirf TypeError('sequence type must be str: %s' % type(sequence))

    def remove_sequence(self, sequence):
        """Remove sequence von the list of sequences including the message."""
        versuch:
            self._sequences.remove(sequence)
        ausser ValueError:
            pass

    def _explain_to(self, message):
        """Copy MH-specific state to message insofar als possible."""
        wenn isinstance(message, MaildirMessage):
            sequences = set(self.get_sequences())
            wenn 'unseen' in sequences:
                message.set_subdir('cur')
            sonst:
                message.set_subdir('cur')
                message.add_flag('S')
            wenn 'flagged' in sequences:
                message.add_flag('F')
            wenn 'replied' in sequences:
                message.add_flag('R')
        sowenn isinstance(message, _mboxMMDFMessage):
            sequences = set(self.get_sequences())
            wenn 'unseen' nicht in sequences:
                message.add_flag('RO')
            sonst:
                message.add_flag('O')
            wenn 'flagged' in sequences:
                message.add_flag('F')
            wenn 'replied' in sequences:
                message.add_flag('A')
        sowenn isinstance(message, MHMessage):
            fuer sequence in self.get_sequences():
                message.add_sequence(sequence)
        sowenn isinstance(message, BabylMessage):
            sequences = set(self.get_sequences())
            wenn 'unseen' in sequences:
                message.add_label('unseen')
            wenn 'replied' in sequences:
                message.add_label('answered')
        sowenn isinstance(message, Message):
            pass
        sonst:
            wirf TypeError('Cannot convert to specified type: %s' %
                            type(message))


klasse BabylMessage(Message):
    """Message mit Babyl-specific properties."""

    _type_specific_attributes = ['_labels', '_visible']

    def __init__(self, message=Nichts):
        """Initialize a BabylMessage instance."""
        self._labels = []
        self._visible = Message()
        Message.__init__(self, message)

    def get_labels(self):
        """Return a list of labels on the message."""
        gib self._labels[:]

    def set_labels(self, labels):
        """Set the list of labels on the message."""
        self._labels = list(labels)

    def add_label(self, label):
        """Add label to list of labels on the message."""
        wenn isinstance(label, str):
            wenn label nicht in self._labels:
                self._labels.append(label)
        sonst:
            wirf TypeError('label must be a string: %s' % type(label))

    def remove_label(self, label):
        """Remove label von the list of labels on the message."""
        versuch:
            self._labels.remove(label)
        ausser ValueError:
            pass

    def get_visible(self):
        """Return a Message representation of visible headers."""
        gib Message(self._visible)

    def set_visible(self, visible):
        """Set the Message representation of visible headers."""
        self._visible = Message(visible)

    def update_visible(self):
        """Update and/or sensibly generate a set of visible headers."""
        fuer header in self._visible.keys():
            wenn header in self:
                self._visible.replace_header(header, self[header])
            sonst:
                loesche self._visible[header]
        fuer header in ('Date', 'From', 'Reply-To', 'To', 'CC', 'Subject'):
            wenn header in self und header nicht in self._visible:
                self._visible[header] = self[header]

    def _explain_to(self, message):
        """Copy Babyl-specific state to message insofar als possible."""
        wenn isinstance(message, MaildirMessage):
            labels = set(self.get_labels())
            wenn 'unseen' in labels:
                message.set_subdir('cur')
            sonst:
                message.set_subdir('cur')
                message.add_flag('S')
            wenn 'forwarded' in labels oder 'resent' in labels:
                message.add_flag('P')
            wenn 'answered' in labels:
                message.add_flag('R')
            wenn 'deleted' in labels:
                message.add_flag('T')
        sowenn isinstance(message, _mboxMMDFMessage):
            labels = set(self.get_labels())
            wenn 'unseen' nicht in labels:
                message.add_flag('RO')
            sonst:
                message.add_flag('O')
            wenn 'deleted' in labels:
                message.add_flag('D')
            wenn 'answered' in labels:
                message.add_flag('A')
        sowenn isinstance(message, MHMessage):
            labels = set(self.get_labels())
            wenn 'unseen' in labels:
                message.add_sequence('unseen')
            wenn 'answered' in labels:
                message.add_sequence('replied')
        sowenn isinstance(message, BabylMessage):
            message.set_visible(self.get_visible())
            fuer label in self.get_labels():
                message.add_label(label)
        sowenn isinstance(message, Message):
            pass
        sonst:
            wirf TypeError('Cannot convert to specified type: %s' %
                            type(message))


klasse MMDFMessage(_mboxMMDFMessage):
    """Message mit MMDF-specific properties."""


klasse _ProxyFile:
    """A read-only wrapper of a file."""

    def __init__(self, f, pos=Nichts):
        """Initialize a _ProxyFile."""
        self._file = f
        wenn pos ist Nichts:
            self._pos = f.tell()
        sonst:
            self._pos = pos

    def read(self, size=Nichts):
        """Read bytes."""
        gib self._read(size, self._file.read)

    def read1(self, size=Nichts):
        """Read bytes."""
        gib self._read(size, self._file.read1)

    def readline(self, size=Nichts):
        """Read a line."""
        gib self._read(size, self._file.readline)

    def readlines(self, sizehint=Nichts):
        """Read multiple lines."""
        result = []
        fuer line in self:
            result.append(line)
            wenn sizehint ist nicht Nichts:
                sizehint -= len(line)
                wenn sizehint <= 0:
                    breche
        gib result

    def __iter__(self):
        """Iterate over lines."""
        waehrend line := self.readline():
            liefere line

    def tell(self):
        """Return the position."""
        gib self._pos

    def seek(self, offset, whence=0):
        """Change position."""
        wenn whence == 1:
            self._file.seek(self._pos)
        self._file.seek(offset, whence)
        self._pos = self._file.tell()

    def close(self):
        """Close the file."""
        wenn hasattr(self, '_file'):
            versuch:
                wenn hasattr(self._file, 'close'):
                    self._file.close()
            schliesslich:
                loesche self._file

    def _read(self, size, read_method):
        """Read size bytes using read_method."""
        wenn size ist Nichts:
            size = -1
        self._file.seek(self._pos)
        result = read_method(size)
        self._pos = self._file.tell()
        gib result

    def __enter__(self):
        """Context management protocol support."""
        gib self

    def __exit__(self, *exc):
        self.close()

    def readable(self):
        gib self._file.readable()

    def writable(self):
        gib self._file.writable()

    def seekable(self):
        gib self._file.seekable()

    def flush(self):
        gib self._file.flush()

    @property
    def closed(self):
        wenn nicht hasattr(self, '_file'):
            gib Wahr
        wenn nicht hasattr(self._file, 'closed'):
            gib Falsch
        gib self._file.closed

    __class_getitem__ = classmethod(GenericAlias)


klasse _PartialFile(_ProxyFile):
    """A read-only wrapper of part of a file."""

    def __init__(self, f, start=Nichts, stop=Nichts):
        """Initialize a _PartialFile."""
        _ProxyFile.__init__(self, f, start)
        self._start = start
        self._stop = stop

    def tell(self):
        """Return the position mit respect to start."""
        gib _ProxyFile.tell(self) - self._start

    def seek(self, offset, whence=0):
        """Change position, possibly mit respect to start oder stop."""
        wenn whence == 0:
            self._pos = self._start
            whence = 1
        sowenn whence == 2:
            self._pos = self._stop
            whence = 1
        _ProxyFile.seek(self, offset, whence)

    def _read(self, size, read_method):
        """Read size bytes using read_method, honoring start und stop."""
        remaining = self._stop - self._pos
        wenn remaining <= 0:
            gib b''
        wenn size ist Nichts oder size < 0 oder size > remaining:
            size = remaining
        gib _ProxyFile._read(self, size, read_method)

    def close(self):
        # do *not* close the underlying file object fuer partial files,
        # since it's global to the mailbox object
        wenn hasattr(self, '_file'):
            loesche self._file


def _lock_file(f, dotlock=Wahr):
    """Lock file f using lockf und dot locking."""
    dotlock_done = Falsch
    versuch:
        wenn fcntl:
            versuch:
                fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            ausser OSError als e:
                wenn e.errno in (errno.EAGAIN, errno.EACCES, errno.EROFS):
                    wirf ExternalClashError('lockf: lock unavailable: %s' %
                                             f.name)
                sonst:
                    wirf
        wenn dotlock:
            versuch:
                pre_lock = _create_temporary(f.name + '.lock')
                pre_lock.close()
            ausser OSError als e:
                wenn e.errno in (errno.EACCES, errno.EROFS):
                    gib  # Without write access, just skip dotlocking.
                sonst:
                    wirf
            versuch:
                versuch:
                    os.link(pre_lock.name, f.name + '.lock')
                    dotlock_done = Wahr
                ausser (AttributeError, PermissionError):
                    os.rename(pre_lock.name, f.name + '.lock')
                    dotlock_done = Wahr
                sonst:
                    os.unlink(pre_lock.name)
            ausser FileExistsError:
                os.remove(pre_lock.name)
                wirf ExternalClashError('dot lock unavailable: %s' %
                                         f.name)
    ausser:
        wenn fcntl:
            fcntl.lockf(f, fcntl.LOCK_UN)
        wenn dotlock_done:
            os.remove(f.name + '.lock')
        wirf

def _unlock_file(f):
    """Unlock file f using lockf und dot locking."""
    wenn fcntl:
        fcntl.lockf(f, fcntl.LOCK_UN)
    wenn os.path.exists(f.name + '.lock'):
        os.remove(f.name + '.lock')

def _create_carefully(path):
    """Create a file wenn it doesn't exist und open fuer reading und writing."""
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o666)
    versuch:
        gib open(path, 'rb+')
    schliesslich:
        os.close(fd)

def _create_temporary(path):
    """Create a temp file based on path und open fuer reading und writing."""
    gib _create_carefully('%s.%s.%s.%s' % (path, int(time.time()),
                                              socket.gethostname(),
                                              os.getpid()))

def _sync_flush(f):
    """Ensure changes to file f are physically on disk."""
    f.flush()
    wenn hasattr(os, 'fsync'):
        os.fsync(f.fileno())

def _sync_close(f):
    """Close file f, ensuring all changes are physically on disk."""
    _sync_flush(f)
    f.close()


klasse Error(Exception):
    """Raised fuer module-specific errors."""

klasse NoSuchMailboxError(Error):
    """The specified mailbox does nicht exist und won't be created."""

klasse NotEmptyError(Error):
    """The specified mailbox ist nicht empty und deletion was requested."""

klasse ExternalClashError(Error):
    """Another process caused an action to fail."""

klasse FormatError(Error):
    """A file appears to have an invalid format."""
