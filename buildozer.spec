[app]
title = 13F SmartScore v1.5
package.name = institutional13fsmart
package.domain = org.quantengine

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.5.0
requirements = python3,kivy==2.3.0,openssl,requests,certifi,urllib3,charset-normalizer,idna

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.accept_sdk_license = True
android.api = 31
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
p4a.branch = develop
