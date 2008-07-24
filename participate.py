#!/usr/bin/env python

#
# Imported modules
#

import getopt, sys
import enact, project

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
    -n<n>, --nice=<n>:  set niceness level increment (default: 10)
    -v, --verbose:      be verbose


Joins a distributed computation project using the project description from the
specified URL.
"""
    sys.exit(code)



#
# Application entry point
#

if __name__ == '__main__':

    nice = 10

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvn',
            ['help', 'verbose', 'nice'])
    except getopt.GetoptError, message:
        sys.stderr.write('Error: %s.\n' % str(message))
        usage(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        if opt in ('-v', '--verbose'):
            verbose = True
        if opt in ('-n', '--nice'):
            try:
                nice = int(arg)
            except ValueError:
                sys.stderr.write('Warning: invalid nice argument; ignored.\n')
    if len(args) <> 1:
        sys.stderr.write('Error: exactly one argument required.\n')
        usage(2)
    project_url, = args
    
    # Process project file
    if verbose:
        print 'Project configuration URL: "%s"...' % project_url
    project = project.Project(project_url)
    if verbose:
        print ('Project selected: "%s" (%s)' % (project.name, project.name))
            
    # Locate the client element for our platform
    if verbose:
        print 'Selecting distribution for platform "%s"...' % sys.platform
    if not project.select_client(sys.platform):
        sys.stderr.write('No client configuration found for platform "%s"!\n' %
            sys.platform)
        sys.exit(1)

    # Change to project directory and synch files
    if verbose:
        print 'Changing to project directory...'
    project.chdir()
    if verbose:
        print 'Updating project files...'
    project.update()

    # Our distribution is complete; start working!
    if verbose:
        print 'Enacting on \"%s:%i\"' % project.server_address, \
            'with command \"%s\"...' % project.command
    enact.enact(project.command, project.server_address,
        project.multiple_results, verbose, nice)


# EOF
