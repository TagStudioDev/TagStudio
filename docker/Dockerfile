FROM ghcr.io/linuxserver/baseimage-kasmvnc:ubuntujammy

WORKDIR /app

# Set environment variables for non-interactive apt-get
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y \
        wget \
        ca-certificates \
        libxcb-cursor-dev \
        locales \
        libxkbcommon-x11-0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-randr0 \
        libxcb-render-util0 \
        libxcb-xinerama0 \
        libxcb-xfixes0 \
        libegl1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Set up the locale
RUN locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8

# Set environment variables to ensure the correct locale is used
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

ENV  FILE_NAME "tagstudio_linux_x86_64.tar.gz"  

# Download the latest release
RUN wget -qO- "https://api.github.com/repos/TagStudioDev/TagStudio/releases/latest" \
    | grep ${FILE_NAME} \
    | grep browser_download_url \
    | cut -d '"' -f 4 \
    | wget -qi -

# Extract the release
RUN tar -zxvf ${FILE_NAME}

# Clean up
RUN rm ${FILE_NAME}

COPY root/ /

ENV TITLE="TagStudio"

CMD tail -f /dev/null
