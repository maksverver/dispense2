#!/usr/bin/env python

#
# Imported modules
#

import getopt
import sys

#
# Global constants
#

EOL = '\n'


#
# Global variables
#

output_verbose    = False
output_remaining  = False
multiple_results  = False
input_file        = None

processed         = {}
ordered_workunits = []


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
    -h, --help:         show this description
    -i<file>, --input=<file>
                        use <file> as the input file containing work units
    -m, --multiple:     expect multiple computation results per work unit
    -r, --remaining     write remaining work units (requires -i, excludes -v)
    -v, --verbose       write verbose output format (excludes -r)


The collect tool collects the computation results from the input provided in
the format produced by the dispense tool. Errors are written to standard error
while the corrected results are written to standard output.

The collect tool performs the following verifications:
    - silently remove identical duplicate results
    - warn for non-matching duplicate results
    - warn for multiple results when working in single result mode
When an input file is provided (with the -i option), the following additional
actions are performed:
    - warn for and remove results for non-existent work units
    - order results according to order of work units in the input file
"""
    sys.exit(code)


def process_results(workunit, results, annotations):
    'Collects the results for a single work unit'
    
    if (not multiple_results) and (len(results) > 1):
        sys.stderr.write('Warning: multiple results for workunit "%s" '
            'in single result mode encountered.\n' % workunit)
        results[:] = results[0:1]   # truncate list to 1 element
    results.sort()

    if (input_file <> None) and (not processed.has_key(workunit)):
        sys.stderr.write('Warning: result encountered for workunit "%s" '
            'which does not occur in the input file.\n' % workunit)
    elif (not multiple_results) and (results == []):
        sys.stderr.write('Warning: zero results for workunit "%s" '
            'in single result mode encountered.\n' % workunit)
    elif (processed.has_key(workunit)) and (processed[workunit] <> None):
        if (processed[workunit][0] <> results):
            sys.stderr.write('Warning: duplicate result for workunit "%s" '
                'does not match result encountered before.\n' % workunit)
    else:
        processed[workunit] = (results, annotations)
        if not input_file:
            if output_verbose:
                for annotation in annotations:
                    sys.stdout.write('%s\n' % annotation)
                sys.stdout.write('>%s\n' % workunit)
                for result in results:
                    sys.stdout.write('<%s\n' % result)
            else:
                for result in results:
                    sys.stdout.write('%s\n' % result)
                if multiple_results:
                    sys.stdout.write('\n')

#
# Application entry point
#

if __name__ == '__main__':

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hi:mrv',
            ['help', 'input', 'multiple', 'remaining', 'verbose'])
    except getopt.GetoptError, message:
        sys.stderr.write('Error: %s.\n' % str(message))
        usage(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        if opt in ('-i', '--input'):
            input_file = arg
        if opt in ('-m', '--multiple'):
            multiple_results = True
        if opt in ('-r', '--remaining'):
            output_remaining = True
        if opt in ('-v', '--verbose'):
            output_verbose = True
    if len(args) <> 0:
        sys.stderr.write('Error: exactly zero arguments required.\n')
        usage(2)
    if output_remaining and output_verbose:
        sys.stderr.write('Error: '
            'only one option of -r and -v may be supplied.\n')
        usage(2)
    if output_remaining and (input_file == None):
        sys.stderr.write('Error: '
            'option -r requires option -i to be supplied.\n')
        usage(2)

    # Read in input file
    if input_file <> None:
        try:
            file = open(input_file, 'rt')
        except IOError, (_, message):
            sys.stderr.write('Error: %s!\n' % message)
            sys.exit(2)

        while True:
            line = file.readline()
            if line == '':
                break
            workunit = line.rstrip('\n')
            if processed.has_key(workunit):
                sys.stderr.write('Warning: '
                    'input file contains duplicate workunit "%s".\n' % workunit)
            else:
                processed[workunit] = None
                ordered_workunits.append(workunit)
        file.close()

    # Process input
    last_workunit    = None
    last_results     = []
    last_annotations = []
    while True:
        line = sys.stdin.readline()
        if line == '':
            if last_workunit <> None:
                process_results(last_workunit, last_results, last_annotations)
            break
        line = line.rstrip('\n')
        if line == '':
            continue
        if line[0] == '>':              # Output (workunit)
            if last_workunit <> None:
                process_results(last_workunit, last_results, last_annotations)
                last_results = []
                last_annotations = []
            last_workunit = line[1:]
        elif line[0] == '<':            # Input (result)
            if last_workunit == None:
                sys.stderr.write('Warning: '
                    'results without corresponding workunit encountered.\n')
            else:
                last_results.append(line[1:])
        else:                           # Annotation
            if last_workunit <> None:
                process_results(last_workunit, last_results, last_annotations)
                last_results = []
                last_annotations = []
                last_workunit = None
            last_annotations.append(line)

    # Generate output with input file
    if input_file:
        for workunit in ordered_workunits:
            if (processed[workunit] == None) and (output_remaining):
                sys.stdout.write('%s\n' % workunit)
            if (processed[workunit] <> None) and (not output_remaining):
                results, annotations = processed[workunit]
                if output_verbose:
                    for annotation in annotations:
                        sys.stderr.write('%s\n' % annotation)
                    sys.stdout.write('>%s\n' % workunit)
                    for result in results:
                        sys.stdout.write('<%s\n' % result)
                else:
                    for result in results:
                        sys.stdout.write('%s\n' % result)
                    if multiple_results:
                        sys.stdout.write('\n')

# EOF
