#!/usr/bin/env python

#
# Imported modules
#

import asynchat, asyncore, getopt, time, socket, sys


#
# Global variables
#

work_buffered = []
work_pending  = []
input         = sys.stdin
output        = sys.stdout


#
# Definitions
#

def usage(code = 0):
    'Displays command line usage information.'

    print 'Usage:\n    %s [<options>]' % sys.argv[0]
    print """
Required arguments:
    None.

Available options:
    -h, --help:             show this description
    -p<n>, --port=<n>:      listen on port <n> (default: 3450)
    -m, --multiple:         expect multiple computation results per work unit
    -r<f>, --resume=<f>:    resume previous session, taking partial results
                            from file <f>

The dispense tool binds on a TCP port and accepts all incoming connections from
enacting applications. Results are output as they become available, in no
predetermined order. The output may contain duplicate results.

To improve the structure of the output, consider processing the output with the
collect tool, which can filter out data and order the results according to the
original input.
"""
    sys.exit(code)


def run(address, multiple_results = False):
    "Runs a project host on the given 'address'."

    server = Dispenser(address, multiple_results)
    try:
        asyncore.loop(timeout=1)
    except asyncore.ExitNow:
        pass

def resume_from_file(results):
    """Removes processed work units in 'results' from the input

    For each line starting with '>' in the 'results' file, lines are read
    from input until the matching work unit is found (or a warning is issused);
    afterwards, all lines read from input but not matched with a result, are
    moved into 'work_buffered' to be served by get_work()."""
    pending = { }
    while True:
        line = results.readline()
        if not line:
            break
        if line[0] <> ">":
            continue
        done = line[1:-1]
        while done not in pending:
            line = input.readline()
            if not line:
                break
            work = line[:-1]
            pending[work] = None
        if done in pending:
            del pending[done]
        else:
            sys.stderr.write( 'Warning: processed work unit "%s" '
                ' does not appear in the input.\n' % work )
    global work_buffered
    work_buffered = pending.keys()


def get_work():
    """Provides an unprocessed work unit.

    This first tries to read a new line of input from the input file. If no
    such line is available, it instead returns a line of input for which no
    result has been returned yet. If no such line exists either, None is
    returned, to indicate that all input has been processed."""

    if work_buffered:
        work = work_buffered.pop(0)
    else:
        line = input.readline()
        if line:
            work = line[:-1]
        else:
            work = None

    if work:
        work_pending.append(work)
    elif work_pending:
        work = work_pending.pop(0)
        work_pending.append(work)
    return work


def put_work(addr, work, results):
    'Stores a processed work unit and it\'s associated result or results.'

    if work in work_pending:
        work_pending.remove(work)
    host, port = addr
    output.write('[%s] %s:%i\n' % (time.ctime(), host, port))
    output.write('>%s\n' % work)
    for result in results:
        output.write('<%s\n' % result)
    output.flush()



class Dispenser(asyncore.dispatcher):
    """Network service that dispenses work units to computing clients.

A listening socket is bound and all incoming connections are dispatched onto
_DispenseSession objects, which handle the connections for the individual
computing clients.
"""

    def __init__(self, addr = ('', 3450), multiple_results = False):
        "Binds a listening socket on the given address 'addr'."

        asyncore.dispatcher.__init__(self)
        self.multiple_results = multiple_results
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(addr)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen(1)


    def handle_accept(self):
        _DispenseSession(self.accept(), self.multiple_results)



class _DispenseSession(asynchat.async_chat):
    'Connection to a single computing client.'

    def __init__(self, (conn, addr), multiple_results = False):
        asynchat.async_chat.__init__(self, conn)
        self.addr             = addr
        self.multiple_results = multiple_results
        self.buffer           = ''
        self.results          = []
        self.set_terminator('\r\n')
        self.send_work()

    def collect_incoming_data(self, data):
        self.buffer = self.buffer + data

    def found_terminator(self):
        'Process a line of output from the computing client.'

        result = self.buffer
        if self.multiple_results:
            if not result:
                # All of multiple results received; send a new work unit
                put_work(self.addr, self.input, self.results)
                self.results = []
                self.send_work()
            else:
                # Store this result
                self.results.append(result)
        else:
            # Single result received; send a new work unit
            put_work(self.addr, self.input, [result])
            self.send_work()
        self.buffer = ''


    def send_work(self):
        'Sends a new work unit to the connected computing client.'

        self.input = get_work()
        if self.input <> None:
            self.push('%s\r\n' % self.input)
        else:
            raise asyncore.ExitNow()



#
# Application entry point
#

if __name__ == '__main__':

    server_host = ''
    server_port = 3450
    multiple_results = False

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hmp:r:',
            ['help', 'multiple', 'port=', 'resume='])
    except getopt.GetoptError, message:
        sys.stderr.write('Error: %s.\n' % message)
        usage(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        if opt in ('-p', '--port'):
            try:
                server_port = int(arg)
            except ValueError:
                sys.stderr.write('Warning: invalid port argument; ignored.\n')
        if opt in ('-m', '--multiple'):
            multiple_results = True
        if opt in ('-r', '--resume'):
            try:
                resume_from_file(file(arg))
            except IOError, e:
                sys.stderr.write('Could not read file "%s": %s.\n', arg, e)
                sys.exit(2)
    if len(args) <> 0:
        sys.stderr.write('Error: exactly zero arguments required.\n')
        usage(2)

    # Start server
    run((server_host, server_port), multiple_results)


# EOF
