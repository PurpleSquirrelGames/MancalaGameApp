These two files are modified to change how buildozer (and python-for-android) behave.

From:
    .buildozer/android/platform/python-for-android/src/templates
The file:
    AndroidManifest.tmpl.xml
Has been modified to remove the "EXTERNAL_STORAGE" permission that is hard-coded
on by default.

From:
    .buildozer/android/platform/python-for-android/dist/mancala/src/org/renpy/android
The file:
    PythonActivity.java
has been modified to NOT delete the pskalah.json settings file between upgrades. See
the resursiveDelete function.

This is a result of a catch-22.

If the file is stored in Internal Storage, then the json file is wiped out at every
upgrade.

If the file is stored in External Storage, then you must:
  a. request permission to see storage in your app.
  b. hope the mobile device does not have a swappable SD Card in it, otherwise
  the file will be lost everytime the end-user does a swap.

These two changes are the only solution I've found.

In theory, one could store the settings to Android's internal SQL system, but that
is far bigger project than I wanted to take on.
