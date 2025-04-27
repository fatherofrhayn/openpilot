# openpilot tools

## System Requirements

openpilot is developed and tested on **Ubuntu 24.04**, which is the primary development target aside from the [supported embedded hardware](https://github.com/commaai/openpilot#running-on-a-dedicated-device-in-a-car).

Most of openpilot should work natively on macOS. On Windows you can use WSL for a nearly native Ubuntu experience. Running natively on any other system is not currently recommended and will likely require modifications.

## Native setup on Ubuntu 24.04 and macOS

**1. Clone openpilot**

NOTE: This repository uses Git LFS for large files. Ensure you have [Git LFS](https://git-lfs.com/) installed and set up before cloning or working with it.

Either do a partial clone for faster download:
``` bash
git clone --filter=blob:none --recurse-submodules --also-filter-submodules https://github.com/commaai/openpilot.git
```

or do a full clone:
``` bash
git clone --recurse-submodules https://github.com/commaai/openpilot.git
```

**2. Run the setup script**

``` bash
cd openpilot
tools/op.sh setup
```

**3. Git LFS**

``` bash
git lfs pull
```

**Development Environment (Docker)**

For a reproducible setup, build and run openpilot inside the Docker container described in the main README:
```bash
# 1. Build the image
docker build -t openpilot-dev .

# 2. Launch an interactive shell in-container
docker run --rm -it \
  -v $(pwd):/openpilot \
  -w /openpilot \
  openpilot-dev

# 3. Inside container, build openpilot:
scons -u -j$(nproc)
```

## WSL on Windows

[Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/about) should provide a similar experience to native Ubuntu. [WSL 2](https://docs.microsoft.com/en-us/windows/wsl/compare-versions) specifically has been reported by several users to be a seamless experience.

Follow [these instructions](https://docs.microsoft.com/en-us/windows/wsl/install) to setup the WSL and install the `Ubuntu-24.04` distribution. Once your Ubuntu WSL environment is setup, follow the Linux setup instructions to finish setting up your environment. See [these instructions](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps) for running GUI apps.

**NOTE**: If you are running WSL and any GUIs are failing (segfaulting or other strange issues) even after following the steps above, you may need to enable software rendering with `LIBGL_ALWAYS_SOFTWARE=1`, e.g. `LIBGL_ALWAYS_SOFTWARE=1 selfdrive/ui/ui`.

## CTF
Learn about the openpilot ecosystem and tools by playing our [CTF](/tools/CTF.md).

## Directory Structure

```
├── ubuntu_setup.sh     # Setup script for Ubuntu
├── mac_setup.sh        # Setup script for macOS
├── cabana/             # View and plot CAN messages from drives or in realtime
├── camerastream/       # Cameras stream over the network
├── joystick/           # Control your car with a joystick
├── lib/                # Libraries to support the tools and reading openpilot logs
├── plotjuggler/        # A tool to plot openpilot logs
├── replay/             # Replay drives and mock openpilot services
├── scripts/            # Miscellaneous scripts
├── serial/             # Tools for using the comma serial
├── sim/                # Run openpilot in a simulator
└── webcam/             # Run openpilot on a PC with webcams
```
