$script = <<SCRIPT
apt update
apt -y upgrade

apt install -y python3 rabbitmq-server amqp-tools make git

# enable rabbitmq cli tools
rabbitmq-plugins enable rabbitmq_management

# set rabbitmq user, vhost and queue
mkdir -p /run/secrets
cp /vagrant/resources/rabbitmq.config /etc/rabbitmq/rabbitmq.config
cp /vagrant/secrets/rabbitmq-definitions.json /run/secrets/rabbitmq-definitions.json
systemctl restart rabbitmq-server

cd /vagrant
make install
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = "debian/stretch64"

  config.vm.define "servicehost" do |master|
    master.vm.network :private_network, ip: "192.168.2.1"
    master.vm.network "forwarded_port", guest: 8080, host: 8080
  end

  config.vm.synced_folder ".", "/vagrant", type: "virtualbox"
  config.vm.provision "shell", inline: $script
end