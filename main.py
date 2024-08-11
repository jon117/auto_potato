import docker
import os
import paramiko
import time
import socket

docker_client = docker.from_env()
docker_enabled = True
docker_image = "python-ssh:latest"
docker_name = "ai-agent-container-python"
docker_ports = {"22/tcp": 50022}
docker_volumes = {os.path.abspath("work_dir"): {"bind": "/root/work_dir", "mode": "rw"}}
ssh_enabled = True
ssh_addr = "localhost"
ssh_port = 50022
ssh_user = "root"
ssh_pass = "toor"
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def build_image():
    try:
        docker_client.images.build(path=".", tag=docker_image, dockerfile="Dockerfile")
        print(f"Image {docker_image} built successfully")
    except docker.errors.BuildError as e:
        print(f"Error building image: {e}")
        return False
    return True

def start_container():
    try:
        # Check if the image exists, if not, build it
        try:
            docker_client.images.get(docker_image)
        except docker.errors.ImageNotFound:
            if not build_image():
                return None

        # Remove existing container if it exists
        existing_containers = docker_client.containers.list(all=True, filters={"name": docker_name})
        if existing_containers:
            print(f"Removing existing container {docker_name}")
            existing_containers[0].remove(force=True)

        # Create a new container
        container = docker_client.containers.run(
            docker_image,
            name=docker_name,
            detach=True,
            ports=docker_ports,
            volumes=docker_volumes,
            working_dir="/root/work_dir"  # Set the working directory
        )
        print(f"Container {docker_name} created and started successfully")
        
        # Print container info for debugging
        container.reload()  # Refresh container information
        print(f"Container ID: {container.id}")
        print(f"Container status: {container.status}")
        print(f"Container ports: {container.ports}")
        
        # Wait for SSH to be ready
        time.sleep(5)
        return container
    except docker.errors.APIError as e:
        print(f"Error with container operation: {e}")
        return None

def connect_ssh():
    max_retries = 5
    for i in range(max_retries):
        try:
            ssh_client.connect(
                ssh_addr,
                port=ssh_port,
                username=ssh_user,
                password=ssh_pass,
                timeout=5
            )
            print("SSH connection established successfully.")
            
            # Verify and set the working directory
            stdin, stdout, stderr = ssh_client.exec_command("pwd")
            current_dir = stdout.read().decode().strip()
            print(f"Current working directory: {current_dir}")
            
            if current_dir != "/root/work_dir":
                print("Changing to the correct working directory...")
                ssh_client.exec_command("cd /root/work_dir")
            
            return True
        except (paramiko.SSHException, socket.error) as e:
            print(f"SSH connection failed (attempt {i+1}/{max_retries}): {e}")
            time.sleep(2)
    return False

def execute_ssh_command(command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    return stdout.read().decode(), stderr.read().decode()

def command_loop():
    while True:
        command = input("Enter a command to execute in the container (/bye to exit): ")
        if command.lower() == '/bye':
            print("Exiting command loop.")
            break
        
        output, error = execute_ssh_command(command)
        print("Output:")
        print(output)
        if error:
            print("Error:")
            print(error)

if __name__ == "__main__":
    container = start_container()
    if container and connect_ssh():
        print("Ready to execute commands")
        command_loop()
        
        # Clean up
        ssh_client.close()
        container.stop()
        container.remove()
        print("Container stopped and removed.")
    else:
        print("Failed to start container or establish SSH connection")
    container = start_container()
    if container and connect_ssh():
        print("Ready to execute commands")
        command_loop()
        
        # Clean up
        ssh_client.close()
        container.stop()
        container.remove()
        print("Container stopped and removed.")
    else:
        print("Failed to start container or establish SSH connection")