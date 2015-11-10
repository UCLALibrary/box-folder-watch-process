# box-folder-watch-process

Use this Python 3 utility to grab a folder from Box.com and generate derivatives of the images and audio files in that folder.

## Installation and Setup

This guide is tailored for Ubuntu 14.04.

1. Make sure python3 and pip3 are installed on the host machine (NOTE: this utility only works with Python 3!)

  ```
  # apt-get install python3 pip3
  ```

2. Install these packages:

  ```
  # apt-get install libmagickwand-dev ffmpeg davfs2 rsync
  # pip3 install pydub Wand
  ```

3. Setup WebDAV, replacing '/path/to/mount/point/', 'your-box-email', and 'your-box-password' as appropriate:

  ```
  # mkdir /path/to/mount/point/
  # echo "https://dav.box.com/dav /path/to/mount/point/ davfs rw,user,noauto 0 0" >> /etc/fstab
  # echo "/path/to/mount/point/ your-box-email your-box-password" >> /etc/davfs2/secrets
  ```

4. Edit 'conf-template' per the instructions in that file.

## Usage

For details:

  ```
  $ python3 box-watch.py -h
  ```
