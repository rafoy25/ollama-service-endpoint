1) Confirm hardware & drivers

Check the GPU and driver on the host:

nvidia-smi


Expected output: a table showing your NVIDIA GPU(s) and driver version. If nvidia-smi is not found or errors, install the official NVIDIA Linux driver for your GPU before continuing. 
NVIDIA Docs
+1

2) Install Docker (if not already installed)

On Ubuntu (example):

# prerequisites
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# add Docker repo and install
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# add your user to docker group (log out/in afterwards)
sudo usermod -aG docker $USER


Verify Docker:

docker version
docker run --rm hello-world

3) Install NVIDIA Container Toolkit (libnvidia-container)

Run the standard apt-based install steps (these are exactly the lines you already have):

# add Nvidia gpg key and repo signing info
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update

# install the toolkit
sudo apt-get install -y nvidia-container-toolkit


These are the official instructions from NVIDIA. 
NVIDIA Docs
+1

4) Configure Docker to use the NVIDIA runtime
# configure Docker to use the nvidia runtime
sudo nvidia-ctk runtime configure --runtime=docker

# restart Docker
sudo systemctl restart docker


You can optionally set the nvidia runtime as the default by adding --set-as-default to the nvidia-ctk command. After restart, Docker will be able to expose GPUs to containers. 
NVIDIA Docs
+1

5) Verify GPU passthrough from Docker

Run a quick test container that calls nvidia-smi inside a container:

docker run --rm --gpus=all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi


Expected: the container prints the same GPU table you saw on the host. If this fails, re-check driver install, toolkit install, and Docker restart. 
NVIDIA Docs
+1

6) Pull & start the Ollama container with GPU

Once verification passes, start Ollama with GPU access:

docker run -d --gpus=all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama


That is the Ollama-recommended GPU run command. If you need a specific tag (e.g., rocm for AMD) see step 9. 
Ollama Documentation

7) Confirm Ollama container sees the GPU and run a model

Check container logs / status:

docker ps -a --filter name=ollama
docker logs ollama --tail 200


Run a model inside the running container:

docker exec -it ollama ollama run llama3


If the model requires CUDA, Ollama should use GPU resources if properly configured. 
Ollama Documentation

8) Common troubleshooting steps

nvidia-smi on host shows driver OK, but container test fails:

Reinstall matching NVIDIA driver for your kernel.

Re-run sudo nvidia-ctk runtime configure --runtime=docker and sudo systemctl restart docker.

Docker permission errors: ensure your user is in docker group or run with sudo.

Check docker info | grep -i nvidia or docker info to see NVIDIA runtime entries. 
NVIDIA Docs
+1

9) Notes about Windows / WSL2 and AMD GPUs

Windows (Docker Desktop + WSL2): Docker Desktop supports GPU access through WSL2 GPU paravirtualization if your Windows, drivers, WSL kernel, and Docker Desktop are updated and WSL2 backend is enabled. For reliable Ollama GPU use, many users prefer a native Linux host or WSL2 + carefully configured Docker Desktop. Practical guides show it can work but may require extra config. 
Docker Documentation
+1

AMD GPUs: Ollama offers a :rocm tag and the example run command:

docker run -d --device /dev/kfd --device /dev/dri \
  -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama:rocm


This requires ROCm drivers and a supported Linux distro. 
Ollama Documentation

10) Quick checklist (copy/paste)
# 1. confirm drivers
nvidia-smi

# 2. install docker (Ubuntu example)
# (paste Docker install block from step 2)

# 3. install nvidia container toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 4. configure runtime and restart docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 5. test nvidia inside container
docker run --rm --gpus=all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# 6. run Ollama with GPU
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

Sources

Ollama Docker docs (run commands & AMD note). 
Ollama Documentation

NVIDIA Container Toolkit install & nvidia-ctk runtime configure usage. 
NVIDIA Docs
+1

Docker Desktop GPU support (WSL2 GPU paravirtualization). 
Docker Documentation