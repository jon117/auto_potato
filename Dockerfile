FROM python:latest

RUN apt-get update && apt-get install -y openssh-server
RUN mkdir /var/run/sshd
RUN echo 'root:toor' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# Set up work directory
RUN mkdir -p /root/work_dir
WORKDIR /root/work_dir

# Set the default directory for SSH sessions
RUN echo "Match User root" >> /etc/ssh/sshd_config && \
    echo "    ChrootDirectory /root" >> /etc/ssh/sshd_config && \
    echo "    ForceCommand cd /work_dir && /bin/bash" >> /etc/ssh/sshd_config

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]