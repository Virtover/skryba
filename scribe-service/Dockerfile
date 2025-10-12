FROM python:3.11
FROM pytorch/pytorch:2.6.0-cuda12.6-cudnn9-runtime

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y
RUN apt-get install -y build-essential curl dos2unix

RUN distribution=$(. /etc/os-release;echo  $ID$VERSION_ID)  && \
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -  && \
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list

RUN apt-get update -y
RUN apt-get install -y nvidia-container-toolkit
RUN mkdir -p /etc/docker
RUN nvidia-ctk runtime configure --runtime=docker

WORKDIR /scribe-service

COPY ./requirements.txt /scribe-service/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /scribe-service/requirements.txt

COPY . /scribe-service
RUN sed -i 's/\r$//' /scribe-service/set_ld_lib_path.sh
RUN chmod +x /scribe-service/set_ld_lib_path.sh && dos2unix /scribe-service/set_ld_lib_path.sh

RUN /bin/bash /scribe-service/set_ld_lib_path.sh

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]