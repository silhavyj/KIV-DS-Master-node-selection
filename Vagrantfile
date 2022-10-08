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
VIEW_IMAGE  = "ds/task01/silhavyj/view:0.1"

NODES = {
    :name_prefix => "node-",
    :subnet => "176.0.1.",
    :ip_offset => 5,
    :image => APP_IMAGE
}

VIEW = {
    :name => "node-view",
    :ip_addr => "176.0.1.2",
    :image => VIEW_IMAGE,
    :config_file => "view/python/config.ini"
}

NODES_COUNT = 4

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.trigger.before :up, type: :command do |trigger|
        File.delete(VIEW[:config_file]) if File.exist?(VIEW[:config_file])
        cfile = File.new(VIEW[:config_file], "w")
        (1..NODES_COUNT).each do |i|
            node_ip_addr = "#{NODES[:subnet]}#{NODES[:ip_offset] + i}"
            cfile.puts "#{node_ip_addr}"
        end
        cfile.close

        trigger.name = "Build docker images"
        trigger.ruby do |env, machine|
            puts "Building node image:"
            `docker build app -t "#{APP_IMAGE}"`
            puts "Building view image:"
            `docker build view -t "#{VIEW_IMAGE}"`
        end
    end

    config.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: ".*/"
    config.ssh.insert_key = false

    config.vm.define VIEW[:name] do |s|
        s.vm.network "private_network", ip: VIEW[:ip_addr]
        # Forward port 80 in the container to port 8080 on the host machine. Listen on 0.0.0.0 (all interfaces)
        s.vm.network "forwarded_port", guest: 5000, host: 8080, host_ip: "0.0.0.0"
        s.vm.hostname = VIEW[:name]
        s.vm.provider "docker" do |d|
          d.image = VIEW[:image]
          d.name = VIEW[:name]
          d.has_ssh = true
        end
        s.vm.post_up_message = "Node #{VIEW[:name]} up and running. You can access the node with 'vagrant ssh #{VIEW[:name]}'}"
    end

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