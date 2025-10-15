# Documentation

## Intialization

We have created a Vagrant file through ```vagrant init``` command. Then add this code : 

```
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
```

By doing ```vagrant up```, This will create three nodes. master node, worker 1 and worker 2. All nodes will have Java 8 and Mongodb pre-installed.

To access nodes : 
- ```vagrant ssh master```
- ```vagrant ssh worker1```
- ```vagrant ssh worker2```


## Installation of hadoop and spark

Do this in all three nodes

```
# Switch to hadoop user
sudo su - hadoop

# Set environment variables
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> ~/.bashrc

# Download and install Hadoop
cd /home/hadoop
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz
tar -xzf hadoop-3.3.4.tar.gz
mv hadoop-3.3.4 hadoop
rm hadoop-3.3.4.tar.gz

# Set Hadoop environment
echo 'export HADOOP_HOME=/home/hadoop/hadoop' >> ~/.bashrc
echo 'export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop' >> ~/.bashrc
echo 'export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin' >> ~/.bashrc

# Download and install Spark
wget https://archive.apache.org/dist/spark/spark-3.3.2/spark-3.3.2-bin-hadoop3.tgz
tar -xzf spark-3.3.2-bin-hadoop3.tgz
mv spark-3.3.2-bin-hadoop3 spark
rm spark-3.3.2-bin-hadoop3.tgz

# Set Spark environment
echo 'export SPARK_HOME=/home/hadoop/spark' >> ~/.bashrc
echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> ~/.bashrc

# Apply environment changes
source ~/.bashrc

# Create required directories
mkdir -p /home/hadoop/hadoop/tmp
mkdir -p /home/hadoop/hadoop/namenode
mkdir -p /home/hadoop/hadoop/datanode

```

## SSH Key setup (Master node only)

```
vagrant ssh master
sudo su - hadoop

# Generate SSH keys
ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa

# Copy keys to all nodes (you'll be prompted for password: hadoop)
ssh-copy-id hadoop@hadoop-master
ssh-copy-id hadoop@hadoop-worker1  
ssh-copy-id hadoop@hadoop-worker2
```

## Hadoop Configuration (Master Node only)

```
# Configure core-site.xml
cat << 'EOF' > $HADOOP_HOME/etc/hadoop/core-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://hadoop-master:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/home/hadoop/hadoop/tmp</value>
    </property>
</configuration>
EOF

# Configure hdfs-site.xml
cat << 'EOF' > $HADOOP_HOME/etc/hadoop/hdfs-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/home/hadoop/hadoop/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/home/hadoop/hadoop/datanode</value>
    </property>
    <property>
        <name>dfs.replication</name>
        <value>2</value>
    </property>
</configuration>
EOF

# Configure yarn-site.xml (NO MapReduce - Pure YARN for Spark)
cat << 'EOF' > $HADOOP_HOME/etc/hadoop/yarn-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <property>
        <name>yarn.resourcemanager.hostname</name>
        <value>hadoop-master</value>
    </property>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.resource.memory-mb</name>
        <value>1536</value>
    </property>
    <property>
        <name>yarn.scheduler.maximum-allocation-mb</name>
        <value>1536</value>
    </property>
    <property>
        <name>yarn.nodemanager.vmem-check-enabled</name>
        <value>false</value>
    </property>
</configuration>
EOF

# Set JAVA_HOME in hadoop-env.sh
echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh

# Configure workers file
cat << 'EOF' > $HADOOP_HOME/etc/hadoop/workers
hadoop-worker1
hadoop-worker2
EOF
```

## Spark Configuration (Master Node only)

```
# Configure Spark defaults (Spark instead of MapReduce)
cat << 'EOF' > $SPARK_HOME/conf/spark-defaults.conf
spark.master                     yarn
spark.driver.memory              512m
spark.yarn.am.memory             512m
spark.executor.memory            512m
spark.executor.cores             1
spark.sql.warehouse.dir          hdfs://hadoop-master:9000/spark-warehouse
EOF

# Configure Spark environment
cat << 'EOF' > $SPARK_HOME/conf/spark-env.sh
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export HADOOP_HOME=/home/hadoop/hadoop
export YARN_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export SPARK_DIST_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath)
EOF
```

## Copy configuration (Master Node only)

```
# Copy Hadoop configurations
for worker in hadoop-worker1 hadoop-worker2; do
    scp -r $HADOOP_HOME/etc/hadoop/* hadoop@$worker:$HADOOP_HOME/etc/hadoop/
done

# Copy Spark configurations  
for worker in hadoop-worker1 hadoop-worker2; do
    scp -r $SPARK_HOME/conf/* hadoop@$worker:$SPARK_HOME/conf/
done
```

## Format HDFS (Master Node only)

```
# Format HDFS (ONLY ONCE)
$HADOOP_HOME/bin/hdfs namenode -format -force
```

## Start Cluster (Master node only)

```
# Start HDFS
$HADOOP_HOME/sbin/start-dfs.sh

# Start YARN  
$HADOOP_HOME/sbin/start-yarn.sh

# Verify cluster
jps
# You should see: NameNode, DataNode, ResourceManager, NodeManager
```
## Verify Cluster Health (Master node only)

```
# Check HDFS health
$HADOOP_HOME/bin/hdfs dfsadmin -report

# Check YARN nodes
$HADOOP_HOME/bin/yarn node -list

# Create HDFS directories for Spark
$HADOOP_HOME/bin/hdfs dfs -mkdir -p /spark-logs
$HADOOP_HOME/bin/hdfs dfs -mkdir -p /spark-warehouse
```

## Download MongoDB Spark Connector (Master node only)

```
# Download MongoDB-Spark connector (instead of HBase)
cd /home/hadoop
wget https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/3.0.2/mongo-spark-connector_2.12-3.0.2.jar

echo "MongoDB Spark Connector downloaded!"
```