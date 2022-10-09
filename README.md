# Distributed master node selection in a cluster
 
This project implements a **selection of a single master node** out of *N* nodes connected to a computer network. This problem was tackled using so-called **election algorithm** where every node can send a message to every other node.

## Running the application

### Requirements

In order to get the whole project up and running, the user is required to have [Vagrant](https://www.vagrantup.com/) and [Docker](https://www.docker.com/) installed on their machine.

### Starting the application

Once the user has installed all the requirements, all they have to do is to navigate to the root folder of the project directory where the Vagrant file is located and run the following command.

```
vagrant up
```

This will automatically start all the containers that make up the project. It has been configured that the containers are built concurrently, meaning that the order in which they start up is not guaranteed and may differ with each start of the application. If you find this undesirable, you can turn the parallelism off by uncommenting line 4 in the Vagrant file.

```
#ENV['VAGRANT_NO_PARALLEL'] = "1"
```

**WARNING**: If you encounter any errors, try to terminate the process using `CTR+C` and running the `vagrant up` command again.

The user can verify that all nodes are up and running using the `docker ps` commands which lists out running containers.

<img src="images/01.png">

#### Changing up the number of nodes

If the user wants to start the application with fewer or more nodes, they can do it by changing the following variable in the Vagrant file (line 31).

```
NODES_COUNT = 6
```

### Clean up

Once the user is done testing the application, they can clean everything up using the following command.

```
vagrant destroy -f
```

This will stop all the running containers this application consists of.

## Structure of the project

