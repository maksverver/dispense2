#!/usr/bin/env python

#
# Imported modules
#

import getopt, os, sys
import dispense, project

#
# Global variables
#

verbose = False


#
# Definitions
#

def usage(code = 0):
    'Displays command line usage information.'

    print 'Usage:\n    %s [<options>] <project-url>' % sys.argv[0]
    print """
Required arguments:
    <project-url>       the URL of the project description file

Available options:
    -h, --help:         show this description
    -v, --verbose:      be verbose
    

Hosts a distributed computation project using the project description from the
specified URL.
"""
    sys.exit(code)


#
# Application entry point
#

if __name__ == '__main__':

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hv',
            ['help', 'verbose'])
    except getopt.GetoptError, message:
        sys.stderr.write('Error: %s.\n' % str(message))
        usage(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        if opt in ('-v', '--verbose'):
            verbose = True
    if len(args) <> 1:
        sys.stderr.write('Error: exactly one argument required.\n')
        usage(2)
    project_url, = args

    # Parse project file
    if verbose:
        print 'Project configuration URL: "%s"...' % project_url
    project = project.Project(project_url)
    if verbose:
        print ('Project selected: "%s" (%s)' % (project.name, project.name))

    # Change to project directory and synch files
    if verbose:
        print 'Changing to project directory...'
    project.chdir()
    if verbose:
        print 'Updating project files...'
    project.update(host = True)
    
    # Our distribution is complete; start hosting!
    if verbose:
        print 'Hosting project on "%s:%s"...' % project.server_address
        print 'Work units are read from "%s".' % project.server_input
        print 'Results are written to "%s".'  % project.server_output
    dispense.input  = file(project.server_input,  'r')
    dispense.output = file(project.server_output, 'a')
    dispense.run(project.server_address, project.multiple_results)


# EOF
