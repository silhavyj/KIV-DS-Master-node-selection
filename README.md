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