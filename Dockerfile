# Dockerfile (development environment)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHON_VERSION=3.11

# Install OS dependencies and build tools
RUN apt-get update && apt-get install -y \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-dev python${PYTHON_VERSION}-venv python3-pip git \
    clang g++ capnproto libcapnp-dev libssl-dev libzmq3-dev \
    qtbase5-dev qttools5-dev qttools5-dev-tools qt5-qmake libqt5x11extras5 libxcb-xinerama0 libxkbcommon-x11-0 libgles2-mesa-dev libegl1-mesa-dev \
    opencl-headers ocl-icd-opencl-dev libeigen3-dev \
    gcc-arm-none-eabi binutils-arm-none-eabi \
  && rm -rf /var/lib/apt/lists/*

# Copy source and build
WORKDIR /openpilot
COPY . .

## Setup Python 3.11 venv for Python dependencies
RUN python3.11 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install numpy protobuf cython \
    && /opt/venv/bin/pip install -r requirements.txt \
    && ln -s /opt/venv .venv

# Use venv Python and tools by default
ENV PATH="/opt/venv/bin:$PATH"

# Build step is now executed interactively inside the container
# Uncomment the following to run during image build if desired
# RUN scons -j$(nproc)

# Default to bash for interactive development
CMD ["/bin/bash"]
