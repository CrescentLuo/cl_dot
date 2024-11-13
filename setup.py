from setuptools import setup

APP = ["extract_obj.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": True,
    # "iconfile": "shark.icns",  # Optional: Path to your app icon file
    "packages": ["pptx", "lxml", "olefile"],
    "excludes": [
        "PyInstaller",
        "PyQt6",
        "zmq",
        "jupyter",
        "jupyter_client",
        "ipykernel",
        "tornado",
        "asyncio",
        "traitlets",
        "ipython",
        "matplotlib",
        "numpy",
        "scipy",
    ],
}

setup(
    app=APP,
    name="ExtractPrism",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
