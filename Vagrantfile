# -*- mode: ruby -*-
# vi: set ft=ruby :

# Configuration for Hadoop + Spark + MongoDB cluster
# 1 Master node (NameNode, ResourceManager, MongoDB Primary)
# 2 Worker nodes (DataNode, NodeManager, MongoDB Secondary)

NUM_WORKERS = 2
MEMORY_MASTER = 4096
MEMORY_WORKER = 2048
CPUS_MASTER = 2
CPUS_WORKER = 1

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/focal64"
  config.vm.box_check_update = false

    # Add this inside Vagrant.configure block but outside the node definitions
  config.vm.synced_folder "/home/ntejha/Music/Projects/City-Mood/project", "/home/hadoop/project", owner: "hadoop", group: "hadoop", mount_options: ["dmode=775,fmode=664"]


  # Common provisioning for all nodes
  config.vm.provision "shell", inline: <<-SHELL
    # Update system
    apt-get update -y
    
    # Add hostnames to /etc/hosts
    echo "192.168.56.10 hadoop-master" >> /etc/hosts
    echo "192.168.56.11 hadoop-worker1" >> /etc/hosts
    echo "192.168.56.12 hadoop-worker2" >> /etc/hosts
    
    # Install Java 8
    apt-get install -y openjdk-8-jdk
    echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> /etc/environment
    
    # Create hadoop user
    useradd -m -s /bin/bash hadoop
    echo 'hadoop:hadoop' | chpasswd
    usermod -aG sudo hadoop
    
    # Install MongoDB tools
    wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-4.4.list
    apt-get update -y
    
    # Disable swap for better performance
    swapoff -a
    sed -i '/ swap / s/^/#/' /etc/fstab
  SHELL

  # Master node configuration
  config.vm.define "master", primary: true do |master|
    master.vm.hostname = "hadoop-master"
    master.vm.network "private_network", ip: "192.168.56.10"
    
    master.vm.provider "virtualbox" do |vb|
      vb.name = "hadoop-master"
      vb.memory = MEMORY_MASTER
      vb.cpus = CPUS_MASTER
      vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    end

    master.vm.provision "shell", inline: <<-SHELL
      # Install MongoDB on master (Primary)
      apt-get install -y mongodb-org
      
      # Configure MongoDB
      sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf
      sed -i 's/#replication:/replication:\\n  replSetName: "rs0"/' /etc/mongod.conf
      
      # Start MongoDB
      systemctl start mongod
      systemctl enable mongod
      
      echo "Master node MongoDB configured"
    SHELL
  end

  # Worker nodes configuration
  (1..NUM_WORKERS).each do |i|
    config.vm.define "worker#{i}" do |worker|
      worker.vm.hostname = "hadoop-worker#{i}"
      worker.vm.network "private_network", ip: "192.168.56.#{10+i}"
      
      worker.vm.provider "virtualbox" do |vb|
        vb.name = "hadoop-worker#{i}"
        vb.memory = MEMORY_WORKER
        vb.cpus = CPUS_WORKER
        vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
        vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
      end

      worker.vm.provision "shell", inline: <<-SHELL
        # Install MongoDB on workers (Secondary)
        apt-get install -y mongodb-org
        
        # Configure MongoDB  
        sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf
        sed -i 's/#replication:/replication:\\n  replSetName: "rs0"/' /etc/mongod.conf
        
        # Start MongoDB
        systemctl start mongod
        systemctl enable mongod
        
        echo "Worker#{i} node MongoDB configured"
      SHELL
    end
  end
end
