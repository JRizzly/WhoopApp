# Copyright (c) 2014 Data Bakery LLC. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
# 
#     1. Redistributions of source code must retain the above copyright notice, this list of
# conditions and the following disclaimer.
# 
#     2. Redistributions in binary form must reproduce the above copyright notice, this list of
# conditions and the following disclaimer in the documentation and/or other materials provided with
# the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY DATA BAKERY LLC ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DATA BAKERY LLC OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# Example invocation.
#
# fab -H 166.78.152.178 -u databakery bootstrap_vm:rackspace=True
# fab -H 166.78.152.178 -u databakery -i ~/.ssh/id_rsa_dwtech bootstrap_vm:rackspace=True
# fab -H 166.78.152.178 -u databakery -i ~/.ssh/id_rsa_dwtech install_app

import os
import subprocess
import time
import signal
import getpass

from fabric.api import local, settings, abort, run, cd, put, env, sudo, prompt, task
from fabric.contrib.files import sed, uncomment, append, upload_template, comment
from fabric.context_managers import prefix, lcd

VIRTUAL_ENV = ". ~/app-pyvenv/bin/activate"


@task
def run_tests():
    # self-contained Flask tests - no servers needed.
    local("python -m unittest discover -v -t tests -s tests/python -p '*_test.py'")

    # live tests against servers with "browsers" - start servers
    local("./manage.py drop -m test")
    local("./manage.py create -m test")
    local("./manage.py load -m test")
    server_process = subprocess.Popen("./manage.py runserver -m test", shell=True, preexec_fn=os.setsid)
    backend_process = subprocess.Popen("./manage.py runbackend -m test", shell=True, preexec_fn=os.setsid)
    time.sleep(1.0) # avoids race conditions
    try:
        local("phantomjs tests/javascript/qunit/run-qunit.js http://localhost:5002/static/html/test.html")
        time.sleep(0.5) # avoids race conditions
        local("casperjs tests/javascript/casper/tests.js")
    finally:
        os.killpg(server_process.pid, signal.SIGTERM)
        os.killpg(backend_process.pid, signal.SIGTERM)

@task
def deploy():
    #run_tests()
    local("git push origin")
    with cd("app"):
        run("git pull origin")
    sudo("supervisorctl restart 'app:*'")

@task
def install_app(rackspace=False):
    run("[ -d app ] || git clone git@github.com:davidkhess/whoop.git app")

    run("[ -d var/run ] || mkdir -p var/run")
    run("[ -d var/log ] || mkdir -p var/log")

    with cd("app"):
        with prefix(VIRTUAL_ENV):
            run("./manage.py generate_secret_key")
            run("./manage.py drop --yes")
            run("./manage.py create")
            run("./manage.py load")
            run("bower install")
            with cd("app/static/vendor/superagent"):
                run("npm install")
                run("make superagent.js")

    upload_template("etc/nginx.conf",
                    "/etc/nginx/sites-enabled/app.conf",
                    use_sudo=True,
                    mode=0644,
                    context={ "username": env.user })
    sudo("chown root:root /etc/nginx/sites-enabled/app.conf")
    sudo("rm /etc/nginx/sites-enabled/default")

    sudo("[ -d /etc/nginx/keys ] || mkdir /etc/nginx/keys")
    put("etc/app.crt", "/etc/nginx/keys", use_sudo=True, mode=0644)
    sudo("chown root:root /etc/nginx/keys/app.crt")
    put("etc/app.key", "/etc/nginx/keys", use_sudo=True, mode=0644)
    sudo("chown root:root /etc/nginx/keys/app.key")

    upload_template("etc/supervisord.conf",
                    "/etc/supervisor/conf.d/app.conf",
                    use_sudo=True,
                    mode=0644,
                    context={ "username": env.user })
    sudo("chown root:root /etc/supervisor/conf.d/app.conf")

    sudo("invoke-rc.d nginx restart")
    sudo("supervisorctl update")
    sudo("supervisorctl restart 'app:*'")

    # Set up lets encrypt.
    if rackspace:
        sudo("git clone https://github.com/letsencrypt/letsencrypt /opt/letsencrypt")
        sudo("mkdir /opt/letsencrypt/.well-known")
        sudo("/opt/letsencrypt/letsencrypt-auto certonly -a webroot --webroot-path=/opt/letsencrypt -d app.justwhoop.com")

        sudo("rm /etc/nginx/keys/app.key")
        sudo("rm /etc/nginx/keys/app.crt")

        sudo("ln -s /etc/letsencrypt/live/app.justwhoop.com/privkey.pem app.key")
        sudo("ln -s /etc/letsencrypt/live/app.justwhoop.com/fullchain.pem app.crt")

        sudo("invoke-rc.d nginx restart")

        put("etc/crontab", "bootstrap")
        sudo("crontab bootstrap/crontab")

def package_installation():
    sudo("apt-get update")
    sudo("apt-get -y upgrade")

    PACKAGES = [
        "postgresql", # Needed on rackspace servers.
        "build-essential",
        "python3.4-venv",
        "python3-dev",
        "libffi-dev",
        "libevent-dev",
        "libxml2-dev",
        "libxslt-dev",
        "python-pip",
        "postgresql-server-dev-9.3",
        "nginx",
        "unzip",
        "ntp",
        "supervisor",
        "git",
        "libfontconfig",
        "ruby",
        "nodejs",
        "npm"
    ]

    sudo("apt-get -y install {}".format(" ".join(PACKAGES)))
    sudo("[ -h /usr/bin/node ] || ln -s /usr/bin/nodejs /usr/bin/node")

    sudo("gem install sass")
    sudo("env TMP=/tmp npm install -g bower")
    sudo("env TMP=/tmp npm install -g uglify-js")

    run("[ -d app-pyvenv ] || pyvenv-3.4 app-pyvenv")

    put("requirements.txt", "bootstrap")
    with cd("bootstrap"):
        with prefix(VIRTUAL_ENV):
            run("pip install --upgrade pip")
            run("pip install -r requirements.txt")

def web_testing_installation():
    # Install phantomjs and casperjs.
    run("[ -d bin ] || mkdir bin")
    with cd("bin"):
        with settings(warn_only=True):
            casper_installed = run("[ -h casperjs ]").return_code == 0

        if not casper_installed:
            run("wget -O casperjs.zip https://github.com/n1k0/casperjs/zipball/1.0.2")
            run("unzip casperjs.zip")
            run("ln -s n1k0-casperjs-bc0da16/bin/casperjs")

        with settings(warn_only=True):
            phantom_installed = run("[ -h phantomjs ]").return_code == 0

        if not phantom_installed:
            run("wget -O phantomjs.tar.bz2 http://phantomjs.googlecode.com/files/phantomjs-1.8.1-linux-x86_64.tar.bz2")
            run("tar jxvf phantomjs.tar.bz2")
            run("ln -s phantomjs-1.8.1-linux-x86_64/bin/phantomjs")    

def misc_setup(rackspace):
    upload_template("etc/postgres_adduser.sql", "bootstrap", context={ "username": env.user })
    upload_template("etc/postgres_setup.sql", "bootstrap", context={ "username": env.user })
    upload_template("etc/postgres_test_setup.sql", "bootstrap", context={ "username": env.user })
    with cd("bootstrap"):
        sudo("psql -f postgres_adduser.sql", user="postgres")    
        sudo("psql -f postgres_setup.sql", user="postgres")    
        sudo("psql -f postgres_test_setup.sql", user="postgres")    

    full_name = prompt("What is your full name?", default="David K. Hess")
    run('git config --global user.name "{}"'.format(full_name))
    email_address = prompt("What is your email address?", default="dhess@data-bakery.com")
    run('git config --global user.email "{}"'.format(email_address))

    uncomment(
        ".bashrc",
        "force_color_prompt=yes"
    )

    append(".bashrc", 'PS1="${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\][\\\$APP_MODE:\w]\[\033[00m\]\$ "')
    append(".bashrc", 'alias v=". ~/app-pyvenv/bin/activate"')
    append(".bashrc", 'alias gl="git log --graph --oneline --all --decorate"')
    append(".profile", 'export APP_MODE=development')
    append(
        "/etc/sudoers",
        [
            "{} ALL=(postgres) NOPASSWD: /usr/bin/psql".format(env.user),
            "{} ALL=NOPASSWD: /usr/bin/supervisorctl".format(env.user)
        ],
        use_sudo=True
    )

    run("[ -d .ssh ] || mkdir -m 0700 .ssh")

    if not rackspace:
        sudo(r'sed -i.bak -e "1 i\\tinker panic 0" /etc/ntp.conf')

@task
def bootstrap_vm(rackspace=False):

    target_user = env.user
    if rackspace:
        with settings(user="root"):

            with settings(warn_only=True):
                user_installed = run("id -u {}".format(target_user)).return_code == 0

            if not user_installed:
                # Add our user account.
                run("adduser --disabled-password -q --gecos={} {}".format(target_user, target_user))
                run("adduser {} sudo".format(target_user))
                password = getpass.getpass("Please enter the password to be set for {}: ".format(target_user))
                run("echo '{}:{}' | chpasswd".format(target_user, password))

            # Pin the kernel. We don't want to update it on a Rackspace VM.
            for pattern in (r"linux-\*", r"grub-\*", r"initramfs-\*"):
                packages = run(r"""dpkg-query --show --showformat='${Package} ${Status}\n' """ + pattern +  r""" | grep " installed" | awk '{ print $1 }'""").strip()
                for package in packages.splitlines():
                    run("echo {} hold | dpkg --set-selections".format(package))
                    run("apt-mark hold {}".format(package))

            # Set the timezone.
            put("etc/timezone", "/etc/timezone")
            run("dpkg-reconfigure --frontend noninteractive tzdata")

    run("[ -d bootstrap ] || mkdir bootstrap")

    package_installation()
    web_testing_installation()
    misc_setup(rackspace)

    run("rm -rf ./bootstrap")

