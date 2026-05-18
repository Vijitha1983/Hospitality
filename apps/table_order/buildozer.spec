[app]
title = Table Order
package.name = tableorder
package.domain = com.hospitality

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0.0

requirements = python3,kivy==2.3.0,requests,urllib3,certifi,charset-normalizer,idna

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
