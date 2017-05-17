# this is where the global settings for the different variants of the PS Kalah
# app are defined.

target_platform = "android_phone"
# target_platform = "android_tablet"
# target_platform = "ios_phone"

img_dir = "assets/img"
if target_platform == "android_tablet":
    img_dir = "assets/large_img"
