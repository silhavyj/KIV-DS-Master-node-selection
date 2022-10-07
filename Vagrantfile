VAGRANTFILE_API_VERSION = "2"

ENV['VAGRANT_DEFAULT_PROVIDER'] = 'docker'
ENV['VAGRANT_NO_PARALLEL'] = "1"
ENV['FORWARD_DOCKER_PORTS'] = "1"
ENV['VAGRANT_EXPERIMENTAL']="typed_triggers"

unless Vagrant.has_plugin?("vagrant-docker-compose")
  system("vagrant plugin install vagrant-docker-compose")
  puts "Dependencies installed, please try the command again."
  exit
end

APP_IMAGE  = "ds/task01/silhavyj/app:0.1"

NODES = {
    :name_prefix => "node-",
    :subnet => "176.0.1.",
    :ip_offset => 1,
    :image => APP_IMAGE
}

NODES_COUNT = 2

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.trigger.before :up, type: :command do |trigger|
        trigger.name = "Build docker images"
        trigger.ruby do |env, machine|
            puts "Building node image:"
            `docker build app -t "#{APP_IMAGE}"`
        end
    end

    config.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: ".*/"
    config.ssh.insert_key = false

    (1..NODES_COUNT).each do |i|
        node_ip_addr = "#{NODES[:subnet]}#{NODES[:ip_offset] + i}"
        node_name = "#{NODES[:name_prefix]}#{i}"
        config.vm.define node_name do |s|
            s.vm.network "private_network", ip: node_ip_addr
            s.vm.hostname = node_name
            s.vm.provider "docker" do |d|
                d.image = NODES[:image]
                d.name = node_name
                d.has_ssh = true
            end
            s.vm.post_up_message = "Node #{node_name} is up and running. You can access the node with 'vagrant ssh #{node_name}'}"
        end
    end
end