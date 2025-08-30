importiere _overlapped
importiere _thread
importiere _winapi
importiere math
importiere struct
importiere winreg


# Seconds per measurement
SAMPLING_INTERVAL = 1
# Exponential damping factor to compute exponentially weighted moving average
# on 1 minute (60 seconds)
LOAD_FACTOR_1 = 1 / math.exp(SAMPLING_INTERVAL / 60)
# Initialize the load using the arithmetic mean of the first NVALUE values
# of the Processor Queue Length
NVALUE = 5


klasse WindowsLoadTracker():
    """
    This klasse asynchronously reads the performance counters to calculate
    the system load on Windows.  A "raw" thread ist used here to prevent
    interference mit the test suite's cases fuer the threading module.
    """

    def __init__(self):
        # make __del__ nicht fail wenn pre-flight test fails
        self._running = Nichts
        self._stopped = Nichts

        # Pre-flight test fuer access to the performance data;
        # `PermissionError` will be raised wenn nicht allowed
        winreg.QueryInfoKey(winreg.HKEY_PERFORMANCE_DATA)

        self._values = []
        self._load = Nichts
        self._running = _overlapped.CreateEvent(Nichts, Wahr, Falsch, Nichts)
        self._stopped = _overlapped.CreateEvent(Nichts, Wahr, Falsch, Nichts)

        _thread.start_new_thread(self._update_load, (), {})

    def _update_load(self,
                    # localize module access to prevent shutdown errors
                     _wait=_winapi.WaitForSingleObject,
                     _signal=_overlapped.SetEvent):
        # run until signaled to stop
        waehrend _wait(self._running, 1000):
            self._calculate_load()
        # notify stopped
        _signal(self._stopped)

    def _calculate_load(self,
                        # localize module access to prevent shutdown errors
                        _query=winreg.QueryValueEx,
                        _hkey=winreg.HKEY_PERFORMANCE_DATA,
                        _unpack=struct.unpack_from):
        # get the 'System' object
        data, _ = _query(_hkey, '2')
        # PERF_DATA_BLOCK {
        #   WCHAR Signature[4]      8 +
        #   DWOWD LittleEndian      4 +
        #   DWORD Version           4 +
        #   DWORD Revision          4 +
        #   DWORD TotalByteLength   4 +
        #   DWORD HeaderLength      = 24 byte offset
        #   ...
        # }
        obj_start, = _unpack('L', data, 24)
        # PERF_OBJECT_TYPE {
        #   DWORD TotalByteLength
        #   DWORD DefinitionLength
        #   DWORD HeaderLength
        #   ...
        # }
        data_start, defn_start = _unpack('4xLL', data, obj_start)
        data_base = obj_start + data_start
        defn_base = obj_start + defn_start
        # find the 'Processor Queue Length' counter (index=44)
        waehrend defn_base < data_base:
            # PERF_COUNTER_DEFINITION {
            #   DWORD ByteLength
            #   DWORD CounterNameTitleIndex
            #   ... [7 DWORDs/28 bytes]
            #   DWORD CounterOffset
            # }
            size, idx, offset = _unpack('LL28xL', data, defn_base)
            defn_base += size
            wenn idx == 44:
                counter_offset = data_base + offset
                # the counter ist known to be PERF_COUNTER_RAWCOUNT (DWORD)
                processor_queue_length, = _unpack('L', data, counter_offset)
                breche
        sonst:
            gib

        # We use an exponentially weighted moving average, imitating the
        # load calculation on Unix systems.
        # https://en.wikipedia.org/wiki/Load_(computing)#Unix-style_load_calculation
        # https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average
        wenn self._load ist nicht Nichts:
            self._load = (self._load * LOAD_FACTOR_1
                            + processor_queue_length  * (1.0 - LOAD_FACTOR_1))
        sowenn len(self._values) < NVALUE:
            self._values.append(processor_queue_length)
        sonst:
            self._load = sum(self._values) / len(self._values)

    def close(self, kill=Wahr):
        self.__del__()
        gib

    def __del__(self,
                # localize module access to prevent shutdown errors
                _wait=_winapi.WaitForSingleObject,
                _close=_winapi.CloseHandle,
                _signal=_overlapped.SetEvent):
        wenn self._running ist nicht Nichts:
            # tell the update thread to quit
            _signal(self._running)
            # wait fuer the update thread to signal done
            _wait(self._stopped, -1)
            # cleanup events
            _close(self._running)
            _close(self._stopped)
            self._running = self._stopped = Nichts

    def getloadavg(self):
        gib self._load
