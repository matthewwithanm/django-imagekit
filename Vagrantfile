# -*- mode: ruby -*-
# vi: set ft=ruby :

# To boot: vagrant up && vagrant ssh
# To run tests: source /vagrant/python /vagrant/setup.py test

$setup_django = <<SCRIPT
cd /vagrant
curl https://bootstrap.pypa.io/get-pip.py | python

pip install virtualenv
virtualenv .env
source .env/bin/activate

pip install django==1.8.17

ln -s /vagrant/ /vagrant/.env/lib/python2.7/site-packages/django-imagekit/
python /vagrant/setup.py install

sudo apt-get install -y \
  build-essential \
  libfreetype6-dev \
  libjpeg8-dev \
  liblcms2-dev \
  libtiff5-dev \
  libwebp-dev \
  python-dev \
  python-tk \
  tcl8.6-dev \
  tk8.6-dev \
  zlib1g-dev \

pip install pillow==2.9

echo "source /vagrant/.env/bin/activate && cd /vagrant/" >> /home/ubuntu/.bashrc
SCRIPT

VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.define :django_imagekit, primary:true do |vbox_config|
    vbox_config.vm.box = "ubuntu/xenial64"
    vbox_config.vm.network "private_network", ip: "10.0.5.25"
    vbox_config.vm.synced_folder ".", "/vagrant", type: "nfs"

    vbox_config.vm.provider :virtualbox do |vb|
      vb.customize ["modifyvm", :id, "--name", "django-imagekit"]
      vb.customize ["modifyvm", :id, "--memory", 2048]
      vb.customize ["modifyvm", :id, "--cpus", 4]
      vb.customize ["modifyvm", :id, "--cpuexecutioncap", "100"]
    end

    vbox_config.vm.provision :shell,
      inline: $setup_django,
      keep_color: true,
      name: 'Setup django'
  end
end
