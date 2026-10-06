[app]
title = 13F SmartScore v1.5
package.name = institutional13fsmart
package.domain = org.quantengine

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.5.0
requirements = python3,kivy,requests,certifi,urllib3

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
