#!/usr/bin/env python

#
# Imported modules
#

import md5, os, urllib, xml.dom.minidom


#
# Definitions
#

def md5_file_string(filepath):
    """Computes the MD5 hash code for the file at 'filepath'.
   
If an exception occurs (the file could not be opened or the hash code could
not be computed) None is returned. Otherwise a string consisting of 32
lower-case hexadecimal characters is returned.
"""

    try:
        md = md5.new()
        f = file(filepath, 'rb')
        while True:
            block = f.read(8192)
            if not block:
                break
            md.update(block)
        return md.hexdigest().lower()
    except:
        return None

        
def _get_flat_elem(elem, name):
    """Returns the text contained in a DOM child element.
    
Given the DOM element 'elem' which has a leaf child element with name 'name',
this returns the contents of the child element. If there is no such element,
None is returned. """

    child_elems = elem.getElementsByTagName(name)
    if not child_elems:
        return None
    else:
        return child_elems[0].firstChild.nodeValue



class Project:
    'The representation of a project description file.'

    def __init__(self, url):
        'Initializes an object from the XML file at the given URL.'
        
        self.doc  = xml.dom.minidom.parse(urllib.urlopen(url))
        
        self.elem = self.doc.firstChild
        self.id   = self.elem.getAttribute('id')
        self.name = self.elem.getAttribute('name')
        self.url  = self.elem.getAttribute('url')
        
        self.server_elem,  = self.elem.getElementsByTagName('server')
        server_host = _get_flat_elem(self.server_elem, 'host')
        server_port = int(_get_flat_elem(self.server_elem, 'port'))
        self.server_address = server_host, server_port
        self.server_input  = _get_flat_elem(self.server_elem, 'input')
        self.server_output = _get_flat_elem(self.server_elem, 'output')

        self.client_elems = self.elem.getElementsByTagName('client')
        self.client_elem  = None

        if _get_flat_elem(self.elem, 'results') == 'multiple':
            self.multiple_results = True
        else:
            self.multiple_results = False
    

    def select_client(self, platform):
        """"Initializes the project for the given client platform.
        
The platform identifier 'platform' is used to select a suitable client
element which is stored in the 'client_elem' attribute. In addition,
the 'platform' and 'command' attributes are set to the platform
identifier and the computing application command respectively.
"""
                
        for client_elem in self.client_elems:
            for platform_elem in client_elem.getElementsByTagName('platform'):
                if platform_elem.firstChild.nodeValue == platform:
                    self.platform    = platform
                    self.client_elem = client_elem
                    self.command     = _get_flat_elem(client_elem, 'command')
                    return True
        return False


    def chdir(self):
        """Changes the current working directory to a project subdirectory.

If a subdirectory with a name equal to the project identifier does not exist,
it is created. The current working directory is then changed to this
subdirectory.
"""
        
        try:
            os.mkdir(self.id)
        except OSError, (code, _):
            if code <> 17:  # 17 == File exists, which is ok
                raise
        os.chdir(self.id)


    def update(self, host = False):
        'Updates all files required for the project.' 
        
        if host:
            self._update(self.server_elem)
        else:
            self._update(self.client_elem)


    def _update(self, elem):
        'Updates all files which are specified under the given DOM element.'
        
        # Download and verify required files
        for file_elem in elem.getElementsByTagName('file'):
            file_url  = file_elem.firstChild.nodeValue
            file_name = file_elem.getAttribute('name')
            file_md   = file_elem.getAttribute('md5').lower()
            file_mode = file_elem.getAttribute('mode')
    
            # Check for existing files
            local_md = md5_file_string(file_name)
            if file_md == local_md:
                continue                # Local file is up to date
            else:
                try:                    # Backup old file                    
                    os.remove(file_name+'.old')
                    os.rename(file_name, file_name+'.old')
                except OSError:
                    pass                # Backup failed; ignore.
    
            # Retrieve remote file
            urllib.urlretrieve(file_url, file_name)
    
            # Verify integrity
            local_md = md5_file_string(file_name)
            if local_md <> file_md:
                raise 'File "%s" failed MD5 checksum!\n' \
                    '\tLocal file:   %s\n\tProject file: %s\n' % \
                    (file_name, local_md, file_md)
                
            # Set file mode
            if file_mode:
                try:
                    os.chmod(file_name, int(file_mode, 8))
                except OSError, error:
                    raise 'Unable to change mode of file "%s" to "%s"!\n' \
                        '%s\n' % (file_name, file_mode, error)
                        
        urllib.urlcleanup()             # Purge urllib caches


# EOF
