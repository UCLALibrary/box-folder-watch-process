'''
box_watch.py

Perform some operations on a Box folder.
'''

# TODO: refactor code into class hierarchy
# or separate global vars (command line args), and functionalize the download
# code.

from argparse import ArgumentParser
from configparser import RawConfigParser
from os.path import splitext
from pydub import AudioSegment
from subprocess import call, check_output, Popen, PIPE
from urllib.parse import urlparse, parse_qs
from wand.image import Image
from wand.display import display

'''
Utility Functions
'''

def NxN_to_tuple(NxN):
    '''
    Convert string of the form NxN to tuple of the form (N, N).
    '''
    partition_tuple = NxN.partition('x')
    return int(partition_tuple[0]), int(partition_tuple[2])


def tuple_to_NxN(tup):
    '''
    Convert tuple of the form (N, N) to string of the form NxN.
    '''
    return str(tup[0]) + 'x' + str(tup[1])

def split_rsync_output(line):
    '''
    Parse a line of output from rsync and pack into a tuple.
    '''
    return line[:11].rstrip(), line[11:].lstrip()

'''
Main Routine
'''

# initialize command line parser
parser = ArgumentParser(description='Perform some operations on a Box folder.')
parser.add_argument('-c', metavar='config', required=True,
    help='absolute path of config file')

# parse command line arguments
args_namespace = parser.parse_args()
config_path = args_namespace.c

# get configfile options
cp = RawConfigParser()
cp.read(config_path)

config_options = {}
for section in cp.sections():
    for option in cp.options(section):
        config_options[option] = cp.get(section, option)

# ensure paths have trailing slashes
mount_point = config_options['mount_point'].rstrip('/') + '/'
sync_src = config_options['sync_src'].rstrip('/') + '/'
sync_dest = config_options['sync_dest'].rstrip('/') + '/'

# turn deriv_sizes string into an array
deriv_sizes = config_options['derivative_sizes'].split(' ') 

image_import_format = config_options['image_import_format']
image_export_format = config_options['image_export_format']
audio_import_format = config_options['audio_import_format']
audio_export_format = config_options['audio_export_format']

try:
    # login to box.com/dav and mount filesystem
    retval = call(['sudo', 'mount', mount_point])

    # set up rsync command to be run as a subprocess
    rsync = [
        'rsync',
        '-avzi',
        '--exclude',
        'lost+found/',
        sync_src,
        sync_dest
        ]

    # convert output from bytestring to string
    rsync_output = [a.decode() for a in check_output(rsync).splitlines()]
    
    # get list of files to create derivatives for
    important = False
    for line in rsync_output:

        # the important lines follow this one
        if 'sending incremental file list' == line:
            important = True
            continue
    
        # there are no more important lines after the empty line
        elif '' == line:
            break
    
        # this line is an action item to create derivatives for
        elif important == True:

            item = split_rsync_output(line)
            action = item[0]
            item_name = item[1]

            # if a new file was added, or
            # if a file was replaced with another of the same name
            if action in ['>f+++++++++', '>f.st......']:
        
                print('Generating derivatives for {}'.format(item_name))

                # split filename into root and extension
                name_root, name_ext = splitext(item_name)
        
                # switch on the file extension
                if '.{}'.format(image_import_format) == name_ext:

                    # generate image derivatives
                    path = '{0}/{1}'.format(sync_src, item_name)
                    with Image(filename=path) as img:

                        # collect image sizes to produce
                        image_sizes = map(NxN_to_tuple, deriv_sizes)

                        for i, target_size in enumerate(image_sizes):

                            current_width = img.size[0]
                            current_height = img.size[1]
                            target_width = target_size[0]
                            target_height = target_size[1]
        
                            with img.clone() as clone:

                                # wide rectangle
                                if current_width > current_height:
                                    # trim off left and right
                                    clone.crop(
                                        (current_width - current_height) // 2,
                                        0,
                                        width=current_height,
                                        height=current_height)

                                # tall rectangle
                                elif current_width < current_height:
                                    # trim off top and bottom
                                    clone.crop(
                                        0,
                                        (current_height - current_width) // 2,
                                        width=current_height,
                                        height=current_height)

                                # if already a square, do nothing
                                else:
                                    pass

                                # scale and save
                                clone.resize(target_width, target_height)
                                clone.save(
                                    filename='{0}/{1}_{2}.{3}'.format(
                                        sync_dest,
                                        name_root,
                                        deriv_sizes[i],
                                        image_export_format))

                        # make one derivative without any transformations
                        with img.clone() as clone:
                            clone.save(
                                filename='{0}/{1}_full.{2}'.format(
                                    sync_dest,
                                    name_root,
                                    image_export_format))
            
                elif '.{}'.format(audio_import_format) == name_ext:

                    # generate audio derivatives
                    export_path = '{0}/{1}.{2}'.format(
                        sync_dest,
                        name_root,
                        audio_export_format)

                    audio = AudioSegment.from_file(
                        '{0}/{1}'.format(sync_src, item_name),
                        audio_import_format)

                    audio.export(export_path, format=audio_export_format)
            
                else:
                    print('Unsupported file format: {}'.format(name_ext))
        
            else:
                print('Unknown action: {}'.format(action))
except Exception as e:
    print(e)

finally:

    # always unmount the box folder
    call(['sudo', 'umount', mount_point])
