# Ollama GPU Setup Guide

A comprehensive guide for running Ollama with GPU support using Docker and NVIDIA Container Toolkit.

---

## Prerequisites

Before beginning, ensure you have:
- An NVIDIA GPU with compatible drivers installed
- Ubuntu or compatible Linux distribution
- Root or sudo access

---

## Step 1: Verify Hardware and Drivers

Check that your GPU and drivers are properly installed:

```bash
nvidia-smi
```

**Expected output:** A table displaying your NVIDIA GPU(s) and driver version.

**If the command fails:** Install the official NVIDIA Linux driver for your GPU before proceeding. Refer to the [NVIDIA Driver Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) for guidance.

---

## Step 2: Install Docker

If Docker is not already installed on your system, follow these steps for Ubuntu:

```bash
# Install prerequisites
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to the docker group (requires logout/login to take effect)
sudo usermod -aG docker $USER
```

**Verify the installation:**

```bash
docker version
docker run --rm hello-world
```

---

## Step 3: Install NVIDIA Container Toolkit

Install the NVIDIA Container Toolkit to enable GPU support in Docker containers:

```bash
# Add NVIDIA GPG key and repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Update package list and install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

For additional information, see the [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

---

## Step 4: Configure Docker Runtime

Configure Docker to use the NVIDIA runtime:

```bash
# Configure the NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker service
sudo systemctl restart docker
```

**Optional:** Add `--set-as-default` flag to the `nvidia-ctk` command to set NVIDIA as the default runtime.

---

## Step 5: Verify GPU Passthrough

Test that Docker can properly access your GPU:

```bash
docker run --rm --gpus=all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

**Expected output:** The container should display the same GPU information table as the host system.

**If this fails:** Review driver installation, toolkit installation, and ensure Docker was restarted properly.

---

## Step 6: Run Ollama with GPU Support

Start the Ollama container with GPU access enabled:

```bash
docker run -d --gpus=all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama
```

This command creates a persistent volume for Ollama data and exposes the service on port 11434.

---

## Step 7: Verify Ollama Installation

Check the container status and logs:

```bash
docker ps -a --filter name=ollama
docker logs ollama --tail 200
```

Test by running a model:

```bash
docker exec -it ollama ollama run llama3
```

If configured correctly, Ollama should utilize GPU resources when running CUDA-enabled models.

---

## Troubleshooting

### GPU Not Detected in Container

If `nvidia-smi` works on the host but fails in containers:

- Reinstall the NVIDIA driver matching your kernel version
- Re-run the runtime configuration: `sudo nvidia-ctk runtime configure --runtime=docker`
- Restart Docker: `sudo systemctl restart docker`

### Permission Errors

Ensure your user is in the docker group or run commands with `sudo`.

### Verify NVIDIA Runtime

Check if the NVIDIA runtime is properly registered:

```bash
docker info | grep -i nvidia
```

---

## Platform-Specific Notes

### Windows with WSL2

Docker Desktop supports GPU access through WSL2 GPU paravirtualization when properly configured. Requirements include updated Windows, drivers, WSL kernel, and Docker Desktop with WSL2 backend enabled. For reliable GPU performance, a native Linux host is often preferred, though WSL2 can work with careful configuration. See [Docker Desktop GPU Documentation](https://docs.docker.com/desktop/gpu/) for details.

### AMD GPUs

Ollama provides a ROCm-enabled image for AMD GPUs:

```bash
docker run -d --device /dev/kfd --device /dev/dri \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama:rocm
```

**Requirements:** ROCm drivers installed on a supported Linux distribution.

---

## Quick Reference Checklist

```bash
# 1. Verify GPU drivers
nvidia-smi

# 2. Install Docker (see Step 2 for full commands)

# 3. Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 4. Configure runtime and restart Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 5. Test GPU access in container
docker run --rm --gpus=all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# 6. Run Ollama with GPU
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

---

## Additional Resources

- [Ollama Docker Documentation](https://github.com/ollama/ollama/blob/main/docs/docker.md)
- [NVIDIA Container Toolkit Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Docker Desktop GPU Support](https://docs.docker.com/desktop/gpu/)

---

*Last updated: October 2025*