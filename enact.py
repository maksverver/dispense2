#!/usr/bin/env python

#
# Imported modules
#

import getopt
import os
import socket
import sys
import time


#
# Definitions
#

def usage(code = 0):
    'Displays command line usage information.'

    print 'Usage:\n    %s [<options>] <command> <host>' % sys.argv[0]
    print """
Required arguments:
    <command>           the command to be executed as the computing application
    <host>              the server host to connect to (hostname or IP address)

Available options:
    -h, --help:         show this description
    -p<n>, --port=<n>:  connect to server on port <n> (default: 3450)
    -m, --multiple:     expect multiple computation results per work unit
    -n<n>, --nice=<n>:  set niceness level increment (default: 10)
    -v, --verbose:      be verbose
"""
    sys.exit(code)



class ConnectionFailure(Exception):
    """"Exception indicating a connection failure.
    
This class has an attribute "value" which contains a more detailed description
of the exceptional situation and a boolean attribute "retry" which indicates
wether or not it makes sense to try to restore the connection.
"""
    
    def __init__(self, value, retry = False):
        self.value = value
        self.retry = retry
        
    def __str__(self):
        return `self.value`
       
       

class ApplicationFailure(Exception):
    """Exception indicating unexpected behaviour from a child process occurred.

This class has an attribute "value" which contains a more detailed description
of the exceptional situation and a boolean attribute "retry" which indicates
wether or not it makes sense to try to restart the application.
"""

    def __init__(self, value, retry = False):
        self.value = value
        self.retry = retry
        
    def __str__(self):
        return `self.value`



class Connection:
    'Represents a connection to a project host.'
    
    def __init__(self, server_addr, multiple_results = False):
        "Initializes a connection to a project host on 'server_addr'."
        
        self.socket = None
        self.connection = None
        self.server_addr = server_addr
        self.multiple_results = multiple_results
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(self.server_addr)
            self.connection = self.socket.makefile('r+')
        except Exception, value:
            raise ConnectionFailure(value, True)


    def get_work(self):
        'Gets a new unit of work from the server (blocks if not available).'

        try:
            return self.connection.readline().rstrip('\r\n')
        except Exception, value:
            raise ConnectionFailure(value, True)


    def put_results(self, results):
        'Returns the results for the last unit of work to the server.'

        try:
            for result in results:
                self.connection.write('%s\r\n' % result)
            if self.multiple_results:
                self.connection.write('\r\n')
            self.connection.flush()
        except Exception, value:
            raise ConnectionFailure(value, True)



class Application:
    'Represents a running computing application.'

    def __init__(self, command, multiple_results = False):
        "Starts a process with the given 'command'."
        
        try:
            self.cmd_in, self.cmd_out = os.popen2(command, 't')
        except Exception, value:
            raise ApplicationFailure(value)
        self.multiple_results = multiple_results


    def put_work(self, work):
        'Sends a work unit to the computing application.'
        
        try:
            self.cmd_in.write('%s\n' % work)
            self.cmd_in.flush()
        except Exception, value:
            raise ApplicationFailure(value, True)
        

    def get_results(self):
        'Gets the computation results from the computing application.'
        
        line = self.cmd_out.readline()
        result = line.rstrip('\n')
        if self.multiple_results:
            results = []
            while result:
                results.append(result)
                line = self.cmd_out.readline()
                result = line.rstrip('\n')
        else:
            results = [result]
        if not line:
            raise ApplicationFailure('computing application terminated', True)
        return results



def enact(command, server_addr, multiple_results = False, verbose = True, nice = 0):
    """Enact on a Dispense2 project.
    
Starts a computing application with the given 'command' and connects to the
project host at 'server_addr'. If 'verbose' is set, warnings are printed to
standard output. If 'nice' is set to a different value than '0', the process
will run with a different 'niceness' (relative process priority); niceness is
not supported under Windows.
"""

    if nice and 'nice' in dir(os):
        os.nice(nice)

    app  = None
    conn = None
    app_delay  = [ 0 ] * 3
    conn_delay = 1
    while True:
        try:
            if not app:
                app = Application(command, multiple_results)
            if not conn:
                conn = Connection(server_addr, multiple_results)

            while True:
                app.put_work(conn.get_work())
                conn.put_results(app.get_results())

        except ApplicationFailure, e:
            if verbose:
                print 'Computing application terminated unexpectedly!'
            app  = None
            conn = None
            if not e.retry:
                raise
            now = time.time()
            if (now - 60 < app_delay[0]):
                if verbose:
                    print 'Over three failures in the past minute: ' \
                        'aborting computation.'
                raise
            app_delay = app_delay[1:] + [now]

        except ConnectionFailure, e:
            if not e.retry:
                if verbose:
                    print 'Connection to host failed!'
                raise
            conn = None
            if verbose:
                print 'Connection to host failed; reconnecting at %s...' % \
                    time.strftime('%H:%M:%S', time.localtime(time.time() + conn_delay))
            for _ in range(conn_delay):
                time.sleep(1)
            conn_delay *= 2
            if conn_delay > 600:
                conn_delay = 600


#
# Application entry point
#

if __name__ == '__main__':

    server_host      = None
    server_port      = 3450
    multiple_results = False
    verbose          = False
    nice             = 10

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hmp:n:v',
            ['help', 'multiple', 'port=', 'nice=', 'verbose'])
    except getopt.GetoptError, message:
        sys.stderr.write('Error: %s.\n' % str(message))
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
        if opt in ('-n', '--nice'):
            try:
                nice = int(arg)
            except ValueError:
                sys.stderr.write('Warning: invalid nice argument; ignored.\n')
        if opt in ('-v', '--verbose'):
            verbose = True
    if len(args) <> 2:
        sys.stderr.write('Error: exactly two arguments required.\n')
        usage(2)
    command, server_host = args

    enact(command, (server_host, server_port), multiple_results, verbose, nice)


# EOF
