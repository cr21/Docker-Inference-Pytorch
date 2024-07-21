# Docker-Inference-Pytorch

## What is Docker?
- Docker provides ability to package, and run application in isolated environment called container. 
- Isolation and security allow to run many container in same host.
- Container are self contained, no need to worrly about underlying Operatiing system, you can share container, share os resources.

## Docker Abstraction

### Docker Image:
- Image is read-only template with instructions of how to create Docker container, Image is often build from another image, and you can customize.
- We can create our own docker image by creating simple `Dockerfile`, and define steps to create image and run instructions.
- Each instruction line in `Dockerfile` creates a layer in image, when we change `Dockerfile` and rebuild image, then only changed layers are recreated and old layers are used from cache, that's why it's lightweight.

### Docker Container
- Container is runnable instance of an image
- We can start, run, create, stop, move, delete a container.

## Installation:
[docker install](https://docs.docker.com/get-docker/)


## Objective
- We will experiment on single build Docker Image and Multi stage Build Docker Image to check docker size can be reduced.
- Reduced size is important for optimizing resources, deployment and security reasons
- We will use pretrained  Pytorch Model trained on Image net to run inference on Image
- We will use  [timm](https://github.com/rwightman/pytorch-image-models.git) models.
- Use [Hydra](https://hydra.cc/) for configuration option passing

## Basic Docker File Single Build 

```Dockerfile
# requirements.txt file content
####################################
torch==1.12.1
torchvision==0.13.1
git+https://github.com/rwightman/pytorch-image-models.git
hydra-core
# Numpy not found error if not using this numpy
numpy==1.26.4

####################################
# Docker file content
####################################

FROM python:3.9.19-slim as stg1

    
COPY requirements.txt .

RUN apt-get update -y && apt install -y --no-install-recommends git\
&& pip install --no-cache-dir -U pip \
    && pip install --user --no-cache-dir -r requirements.txt

WORKDIR /src

COPY . .

ENTRYPOINT ["python3", "inference.py"]

```

**Image size : 2.06 GB**

- this image downloads `torch-1.12.1-cp39-cp39-manylinux1_x86_64.whl` manylinux distribution from [pytorch build whls](https://download.pytorch.org/whl/torch_stable.html)


##  Single Build Docker with  platform specefic wheels - Reduced size by 1GB


```Dockerfile
# requirements.txt file content
####################################
git+https://github.com/rwightman/pytorch-image-models.git
hydra-core
# Numpy not found error if not using this numpy
numpy==1.26.4

####################################
# Docker file content
####################################

FROM python:3.9.19-slim as build

    
COPY requirements.txt .

RUN apt-get update -y && apt install -y --no-install-recommends git\
&& pip install --no-cache-dir -U pip && pip install --user --no-cache-dir https://download.pytorch.org/whl/cpu/torch-1.11.0%2Bcpu-cp39-cp39-linux_x86_64.whl \
    && pip install --user --no-cache-dir https://download.pytorch.org/whl/cpu/torchvision-0.12.0%2Bcpu-cp39-cp39-linux_x86_64.whl \
    && pip install --user --no-cache-dir -r requirements.txt

WORKDIR /src

COPY . .

ENTRYPOINT ["python3", "inference.py"]
```


**Image size : 1.01 GB**

- this image downloads `/cpu/torch-1.11.0%2Bcpu-cp39-cp39-linux_x86_64.whl ` linux_x86_64 architecture distribution from [torchpy39 build whls](https://download.pytorch.org/whl/cpu/torch-1.11.0%2Bcpu-cp39-cp39-linux_x86_64.whl )
- this image downloads `/cpu/torchvision-0.12.0%2Bcpu-cp39-cp39-linux_x86_64.whl ` linux_x86_64 architecture distribution from [torchvisionpy39 build whls](https://download.pytorch.org/whl/cpu/torchvision-0.12.0%2Bcpu-cp39-cp39-linux_x86_64.whl  )


## muti-stage Build with Many Linux Image (Not much reduction 1.94GB)


```Dockerfile
# requirements.txt file content
####################################
torch==1.12.1
torchvision==0.13.1
git+https://github.com/rwightman/pytorch-image-models.git
hydra-core
# Numpy not found error if not using this numpy
numpy==1.26.4

####################################
# Docker file content
####################################

# multi stage build https://pythonspeed.com/articles/multi-stage-docker-python/
# Stage 1: install pytorch git and requirementes.txt 
# then copy only libraries in second stage
FROM python:3.9.19-slim as stg1

    
COPY requirements.txt .

RUN apt-get update -y && apt install -y --no-install-recommends git\
&& pip install --no-cache-dir -U pip \
    && pip install --user --no-cache-dir -r requirements.txt

# Stage 2: run application code
FROM python:3.9.19-slim

COPY --from=stg1 /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

WORKDIR /src

COPY . .

ENTRYPOINT ["python3", "inference.py"]


```

**Image size 1.94 GB**

- in first stage we only installed dependencies and only copied necessary depedencies in second stage which reduced size.
- size reduction is not so much, but we will see how this further decreased using
platform specefic torch libraries.

##  Multi Stage Build Docker with  platform specefic wheels - Reduced size < 1GB (894 MB)


```Dockerfile
# requirements.txt file content
####################################
git+https://github.com/rwightman/pytorch-image-models.git
hydra-core
# Numpy not found error if not using this numpy
numpy==1.26.4

####################################
# Docker file content
####################################

# multi stage build https://pythonspeed.com/articles/multi-stage-docker-python/
# Stage 1: install pytorch git and requirementes.txt 
# then copy only libraries in second stage
FROM python:3.9.19-slim as stg1

    
COPY requirements.txt .

RUN apt-get update -y && apt install -y --no-install-recommends git\
&& pip install --no-cache-dir -U pip && pip install --user --no-cache-dir https://download.pytorch.org/whl/cpu/torch-1.11.0%2Bcpu-cp39-cp39-linux_x86_64.whl \
    && pip install --user --no-cache-dir https://download.pytorch.org/whl/cpu/torchvision-0.12.0%2Bcpu-cp39-cp39-linux_x86_64.whl \
    && pip install --user --no-cache-dir -r requirements.txt

# Stage 2: run application code
FROM python:3.9.19-slim

COPY --from=stg1 /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

WORKDIR /src

COPY . .

ENTRYPOINT ["python3", "inference.py"]

```
**Image size : 894 MB**

- multi stage build with installing platform specific libraries reduced image size < 900 MB.
- We reduced Image size from 2.06 GB to 894 MB, which is huge reduction.


## Experiment

```
REPOSITORY                                             TAG       IMAGE ID       CREATED          SIZE
timm-pytorch-multi-stage-build-cpu-py39-linux-x86_64   latest    5a36bed12b2b   4 seconds ago    894MB
timm-pytorch-multi-stage-build-many-linux              latest    137cb67745e8   9 minutes ago    1.94GB
timm-pytorch-singe-stage-recued-cpu-py3.9-wheels       latest    c0108460ca06   17 minutes ago   1.01GB
timm-pytorch-singe-stage-many-linux                    latest    83b57dcf004b   27 minutes ago   2.06GB
```

# How to build & run docker Image
```
1. Build Docker Image

docker build --tag <TAG_NAME> .

e.g 

docker build --tag timm-pytorch-multi-stage-build-cpu-py39-linux-x86_64  .

2. Run Docker Image with default params

docker run -it <IMAGE_NAME>

e.g 

docker run  -it timm-pytorch-multi-stage-build-cpu-py39-linux-x86_64 


### Docker run with parameters overriding hydra config.yaml files

docker run -it <IMAGE_NAME> model=<MODEL_NAME_FROM_TIMM> image=<IMAGE_URI>

e.g

docker run -it timm-pytorch-multi-stage-build-cpu-py39-linux-x86_64 model=resnet152 image=https://github.com/pytorch/hub/raw/master/images/dog.jpg

```

# Docker Hub Image


[Docker Hub Image - timm-pytorch-docker-multi-stage-build](https://hub.docker.com/repository/docker/crtagadiya/timm-pytorch-docker-multi-stage-build/general)


# Reference

- [Multi-stage-docker-python](https://pythonspeed.com/articles/multi-stage-docker-python/)
- [Hydra](https://hydra.cc/)
- [Docker](https://docs.docker.com/guides/docker-concepts/building-images/understanding-image-layers/)
