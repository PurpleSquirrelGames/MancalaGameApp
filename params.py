# this is where the global settings for the different variants of the PS Kalah
# app are defined.

target_platform = "android_phone"
# target_platform = "android_tablet"
# target_platform = "ios_phone"

target_language = "en_US"  # English
# target_language = "es_ES"   # Spanish
# target_language = "zh_CN"   # Mandarin Chinese
# target_language = "fr_HT"   # Hatian French Creole
# target_language = "he_IL"   # Hebrew
# target_language = "ar_001"  # Arabic (World)

img_dir = "assets/img"
if target_platform == "android_tablet":
    img_dir = "assets/large_img"
