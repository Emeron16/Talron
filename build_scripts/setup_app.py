"""
Setup script for creating a Mac .app bundle using py2app.
Run: python setup_app.py py2app
"""
from setuptools import setup

APP = ['run_game_gui.py']
DATA_FILES = [
    ('assets', ['src/ui/assets/background_video.mp4', 'src/ui/assets/background_music.mp3']),
]
OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'tkinter',
        'src',
        'src.models',
        'src.services',
        'src.data',
        'src.ui',
        'dataclasses',
        'typing',
        'json',
        'pathlib',
    ],
    'includes': [
        'pygame',
        'cv2',
        'PIL',
    ],
    'excludes': [
        'pytest',
        'hypothesis',
        'tests',
    ],
    'plist': {
        'CFBundleName': 'Talron Word Search',
        'CFBundleDisplayName': 'Talron Word Search',
        'CFBundleGetInfoString': 'A themed word search puzzle game',
        'CFBundleIdentifier': 'com.emeronmarcelle.talron',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 Emeron Marcelle. All rights reserved.',
        'NSHighResolutionCapable': True,
    },
    # 'iconfile': 'app_icon.icns',  # Optional: Uncomment and create this file for custom icon
}

setup(
    name='Talron Word Search',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
