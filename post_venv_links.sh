#!/bin/bash

# For kivy to work inside the virtual environment on linux mint 18
# some system packages have to be linked.

DIR=`pwd`
SYS_PACKAGES=/usr/lib/python2.7/dist-packages
VENV_PACKAGES=$DIR/venv/lib/python2.7/site-packages

ln -s $SYS_PACKAGES/buildozer $VENV_PACKAGES
ln -s $SYS_PACKAGES/Cython $VENV_PACKAGES
ln -s $SYS_PACKAGES/garden $VENV_PACKAGES
ln -s $SYS_PACKAGES/kivy $VENV_PACKAGES
ln -s $SYS_PACKAGES/plyer $VENV_PACKAGES
