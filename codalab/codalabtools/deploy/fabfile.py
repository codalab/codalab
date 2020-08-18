"""
Defines deployment commands.
"""

import logging
import logging.config
import os
from os.path import (abspath, dirname)
import sys

# Add codalabtools to the module search path
import pwd

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))

from io import StringIO
from fabric.api import (cd,
                        env,
                        execute,
                        get,
                        prefix,
                        put,
                        require,
                        task,
                        roles,
                        require,
                        run,
                        local,
                        settings,
                        shell_env,
                        sudo)
from fabric.contrib.files import exists
from codalabtools.deploy import DeploymentConfig, Deployment

logger = logging.getLogger('codalabtools')


@task
def using(path):
    """
    Specifies a location for the CodaLab configuration file (e.g., deployment.config)
    """
    env.cfg_path = path


@task
def config(label):
    """
    Reads deployment parameters for the given setup.
    label: Label identifying the desired setup (e.g., prod, test, etc.)
    """
    env.cfg_label = label
    print("Deployment label is:", env.cfg_label)
    print("Loading configuration from:", env.cfg_path)
    configuration = DeploymentConfig(label, env.cfg_path)
    print("Configuring logger...")
    logging.config.dictConfig(configuration.getLoggerDictConfig())
    logger.info("Loaded configuration from file: %s", configuration.getFilename())
    env.roledefs = {'web': configuration.getWebHostnames()}

    # Credentials
    env.user = configuration.getVirtualMachineLogonUsername()

    # Repository
    env.git_codalab_tag = configuration.getGitTag()
    env.deploy_codalab_dir = 'codalab-competitions'  # Directory for codalab competitions

    env.django_settings_module = 'codalab.settings'
    env.django_configuration = configuration.getDjangoConfiguration()  # Prod or Test
    env.config_http_port = '80'
    env.config_server_name = "{0}.cloudapp.net".format(configuration.getServiceName())
    print("Deployment configuration is for:", env.config_server_name)

    env.configuration = True
    env.SHELL_ENV = {}


def setup_env():
    env.SHELL_ENV.update(dict(
        DJANGO_SETTINGS_MODULE=env.django_settings_module,
        DJANGO_CONFIGURATION=env.django_configuration,
        CONFIG_HTTP_PORT=env.config_http_port,
        CONFIG_SERVER_NAME=env.config_server_name,
    ))
    return prefix('source ~/%s/venv/bin/activate' % env.deploy_codalab_dir), shell_env(**env.SHELL_ENV)


############################################################
# Installation (one-time)


def provision_packages(packages=None):
    """
    Installs a set of packages on a host machine. Web servers and compute workers.

    packages: A string listing the packages which will get installed with the command:
        sudo apt-get -y install <packages>
    """
    sudo('apt-get update')
    sudo('apt-get -y upgrade')
    sudo('apt-get install -y python-pip')
    sudo('apt-get -y install %s' % packages)
    sudo('apt-get -y install git')
    sudo('apt-get -y install python-virtualenv')
    sudo('apt-get -y install virtualenvwrapper')
    sudo('apt-get -y install python-setuptools')
    sudo('apt-get -y install build-essential')
    sudo('apt-get -y install python-dev')


@task
def provision_web_packages():
    """
    Installs required software packages on a newly provisioned web instance.
    """
    packages = ('libjpeg-dev nginx supervisor xclip zip libmysqlclient-dev uwsgi-plugin-python')
    provision_packages(packages)


@task
def provision_compute_workers_packages():
    """
    Installs required software packages on a newly provisioned compute worker machine.
    """
    packages = ('python-crypto libpcre3-dev libpng12-dev libjpeg-dev libmysqlclient-dev uwsgi-plugin-python libsm6 openjdk-7-jre unixodbc unixodbc-dev')

    ubuntu_version = run('cat /etc/issue')
    if not ubuntu_version.startswith("Ubuntu 14.04"):
        # Upstart not default on versions > 14.04
        packages += ' upstart upstart-sysv'
    provision_packages(packages)


@roles('web')
@task
def provision_web():
    '''
    Install everything from scratch (idempotent).
    '''
    # Install Linux packages
    provision_web_packages()

    # Setup repositories
    def ensure_repo_exists(repo, dest):
        run('[ -e %s ] || git clone %s %s' % (dest, repo, dest))
    ensure_repo_exists('https://github.com/codalab/codalab-competitions', env.deploy_codalab_dir)

    # Initial setup
    with cd(env.deploy_codalab_dir):
        run('git checkout %s' % env.git_codalab_tag)
        run('./dev_setup.sh')

    # Install mysql database
    install_mysql()
    # Deploy!
    _deploy()
    nginx_restart()
    supervisor('stop')
    supervisor('start')


@task
def provision_compute_worker(label):
    '''
    Install compute workers from scracth. Run only once
    '''
    # Install packages
    sudo("add-apt-repository ppa:openjdk-r/ppa --yes")
    sudo("apt-get update")
    provision_compute_workers_packages()
    env.deploy_codalab_dir = 'codalab-competitions'

    # Setup repositories
    def ensure_repo_exists(repo, dest):
        run('[ -e %s ] || git clone %s %s' % (dest, repo, dest))
    ensure_repo_exists('https://github.com/codalab/codalab-competitions', env.deploy_codalab_dir)

    # If you need to install upstart, run this:
    #     sudo apt-get install upstart-sysv
    #     sudo update-initramfs -u
    #     sudo reboot

    deploy_compute_worker(label=label)
    download_install_anaconda_library()
    install_coco_api()
    setup_compute_worker_user()
    setup_compute_worker_permissions()


@task
def deploy_compute_worker(label):
    '''
    Deploy/update compute workers.
    For monitoring make sure the azure instance has the port 8000 forwarded

    :param label: Either test or prod
    '''
    env.deploy_codalab_dir = 'codalab-competitions'
    # Create .codalabconfig within home directory
    env.label = label
    cfg = DeploymentConfig(env.label, env.cfg_path if hasattr(env, 'cfg_path') else '.codalabconfig')
    dep = Deployment(cfg)
    buf = StringIO()
    buf.write(dep.get_compute_workers_file_content())
    settings_file = os.path.join('~', '.codalabconfig')
    put(buf, settings_file)
    env.git_codalab_tag = cfg.getGitTag()
    env.logs_password = cfg.get_compute_worker_logs_password()

    # Initial setup
    with cd(env.deploy_codalab_dir):
        run('git checkout %s' % env.git_codalab_tag)
        run('git pull')

        # make sure we remove old version, added 2/20/17 can remove a while after that
        run('source /home/azureuser/codalab-competitions/venv/bin/activate && pip uninstall django-storages && pip uninstall django-storages-redux', warn_only=True)

        run('source /home/azureuser/codalab-competitions/venv/bin/activate && pip install --upgrade pip && pip install -r /home/azureuser/codalab-competitions/codalab/requirements/dev_azure.txt')

        # run('./dev_setup.sh')

    # run("source /home/azureuser/codalab-competitions/venv/bin/activate && pip install bottle==0.12.8")

    current_directory = os.path.dirname(os.path.realpath(__file__))

    # Adding compute worker upstart config
    broker_url = cfg.get_broker_url()
    compute_worker_conf_template = open('{}/configs/upstart/codalab-compute-worker.conf'.format(current_directory)).read()
    compute_worker_conf = compute_worker_conf_template.format(
        broker_url=broker_url
    )
    compute_worker_conf_buf = StringIO()
    compute_worker_conf_buf.write(compute_worker_conf)
    put(
        local_path=compute_worker_conf_buf,  # Path can be a file-like object, in this case our processed template
        remote_path='/etc/init/codalab-compute-worker.conf',
        use_sudo=True
    )

    # Adding codalab monitor upstart config  ### No longer needed!
    # put(
    #     local_path='{}/configs/upstart/codalab-monitor.conf'.format(current_directory),
    #     remote_path='/etc/init/codalab-monitor.conf',
    #     use_sudo=True
    # )
    # run("echo %s > /home/azureuser/codalab-competitions/codalab/codalabtools/compute/password.txt" % env.logs_password)

    with settings(warn_only=True):
        sudo("stop codalab-compute-worker")
        sudo("stop codalab-monitor")  # just in case it's left from a previous install
        sudo("start codalab-compute-worker")
        # sudo("start codalab-monitor")


@roles('web')
@task
def install_mysql(choice='all'):
    """
    Installs a local instance of MySQL of the web instance. This will only work
    if the number of web instances is one.

    choice: Indicates which assets to create/install:
        'mysql'      -> just install MySQL; don't create the databases
        'website_db' -> just create the website database
        'all' or ''  -> install everything
    """
    require('configuration')
    if len(env.roledefs['web']) != 1:
        raise Exception("Task install_mysql requires exactly one web instance.")

    if choice == 'mysql':
        choices = {'mysql'}
    elif choice == 'website_db':
        choices = {'website_db'}
    elif choice == 'all':
        choices = {'mysql', 'website_db'}
    else:
        raise ValueError("Invalid choice: %s. Valid choices are: 'build', 'web' or 'all'." % (choice))

    configuration = DeploymentConfig(env.cfg_label, env.cfg_path)
    dba_password = configuration.getDatabaseAdminPassword()

    if 'mysql' in choices:
        sudo('DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server')
        sudo('mysqladmin -u root password {0}'.format(dba_password))

    if 'website_db' in choices:
        db_name = configuration.getDatabaseName()
        db_user = configuration.getDatabaseUser()
        db_password = configuration.getDatabasePassword()
        cmds = ["create database {0};".format(db_name),
                "create user '{0}'@'localhost' IDENTIFIED BY '{1}';".format(db_user, db_password),
                "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'localhost' WITH GRANT OPTION;".format(db_name, db_user)]
        run('mysql --user=root --password={0} --execute="{1}"'.format(dba_password, " ".join(cmds)))


############################################################
# Deployment

@roles('web')
@task
def supervisor(command):
    """
    Starts the supervisor on the web instances.
    """
    env_prefix, env_shell = setup_env()
    with env_prefix, env_shell, cd(env.deploy_codalab_dir):
        if command == 'start':
            run('mkdir -p ~/logs')
            run('supervisord -c codalab/config/generated/supervisor.conf')
        elif command == 'stop':
            run('supervisorctl -c codalab/config/generated/supervisor.conf stop all')
            run('supervisorctl -c codalab/config/generated/supervisor.conf shutdown')
            # HACK: since competition worker is multithreaded, we need to kill all running processes
            with settings(warn_only=True):
                run('pkill -9 -f worker.py')
        elif command == 'restart':
            run('supervisorctl -c codalab/config/generated/supervisor.conf restart all')
        else:
            raise 'Unknown command: %s' % command


@roles('web')
@task
def nginx_restart():
    """
    Restarts nginx on the web server.
    """
    sudo('/etc/init.d/nginx restart')


# Maintenance and diagnostics
@roles('web')
@task
def maintenance(mode):
    """
    Begin or end maintenance (mode is 'begin' or 'end')
    """
    modes = {'begin': '1', 'end': '0'}
    if mode not in modes:
        print("Invalid mode. Valid values are 'begin' or 'end'")
        sys.exit(1)

    require('configuration')
    env.SHELL_ENV['MAINTENANCE_MODE'] = modes[mode]

    # Update nginx.conf
    env_prefix, env_shell = setup_env()
    with env_prefix, env_shell, cd(env.deploy_codalab_dir), cd('codalab'):
        run('python manage.py config_gen')

    nginx_restart()


@roles('web')
@task
def deploy():
    """
    Put a maintenance message, deploy, and then restore website.
    """
    get_database_dump()
    maintenance('begin')
    supervisor('stop')
    _deploy()
    supervisor('start')
    maintenance('end')


def _deploy():
    # Update competition website
    # Pull branch and run requirements file, for info about requirments look into dev_setp.sh
    env_prefix, env_shell = setup_env()
    with env_prefix, env_shell, cd(env.deploy_codalab_dir):
        run('git checkout %s' % env.git_codalab_tag)
        run('git pull')
        run('./dev_setup.sh')

    # Create local.py
    cfg = DeploymentConfig(env.cfg_label, env.cfg_path)
    dep = Deployment(cfg)
    buf = StringIO()
    buf.write(dep.getSettingsFileContent())
    # local.py is generated here. For more info about content look into deploy/__.init__.py
    settings_file = os.path.join(env.deploy_codalab_dir, 'codalab', 'codalab', 'settings', 'local.py')
    put(buf, settings_file)

    # Update the website configuration
    env_prefix, env_shell = setup_env()
    with env_prefix, env_shell, cd(env.deploy_codalab_dir), cd('codalab'):
        # make sure we remove old version, added 2/20/17 can remove a while after that
        run('pip uninstall django-storages && pip uninstall django-storages-redux && pip install django-storages-redux==1.3.2', warn_only=True)

        sudo('apt-get install -y nodejs-legacy npm')
        run('npm install')
        run('npm run build-css')

        # Generate configuration files (bundle_server_config, nginx, etc.)
        # For more info look into https://github.com/greyside/django-config-gen
        run('python manage.py config_gen')
        # Migrate database
        run('python manage.py syncdb --migrate')
        # Create static pages
        run('python manage.py collectstatic --noinput')
        # For sending email, have the right domain name.
        run('python manage.py set_site %s' % cfg.getSslRewriteHosts()[0])
        # Put nginx and supervisor configuration files in place, ln creates symbolic links
        sudo('ln -sf `pwd`/config/generated/nginx.conf /etc/nginx/sites-enabled/codalab.conf')
        sudo('ln -sf `pwd`/config/generated/supervisor.conf /etc/supervisor/conf.d/codalab.conf')
        # Setup new relic
        run('newrelic-admin generate-config %s newrelic.ini' % cfg.getNewRelicKey())

    # Install SSL certficates (/etc/ssl/certs/)
    require('configuration')
    if (len(cfg.getSslCertificateInstalledPath()) > 0) and (len(cfg.getSslCertificateKeyInstalledPath()) > 0):
        put(cfg.getSslCertificatePath(), cfg.getSslCertificateInstalledPath(), use_sudo=True)
        put(cfg.getSslCertificateKeyPath(), cfg.getSslCertificateKeyInstalledPath(), use_sudo=True)
    else:
        logger.info("Skipping certificate installation because both files are not specified.")


# UTILITIES FAB COMMAND
# MOSTLY USED ON COMPUTE WORKERS

@task
def setup_compute_worker_user():
    # Steps to setup compute worker:
    #   1) setup_compute_worker_user (only run this once as it creates a user and will probably fail if re-run)
    #   2) setup_compute_worker_permissions

    # Try to get user...
    result = run('grep "^workeruser:" /etc/passwd', warn_only=True)
    if not result:
        # User not found, create them
        sudo('adduser --quiet --disabled-password --gecos "" workeruser')
        sudo('echo workeruser:password | chpasswd')


@task
def download_install_anaconda_library():
    '''
    Download anaconda package to compute workers.
    '''
    if not exists("/home/azureuser/anaconda/"):
        with cd('/home/azureuser'):
            sudo("wget http://repo.continuum.io/archive/Anaconda2-2.4.0-Linux-x86_64.sh")
            sudo("bash Anaconda2-2.4.0-Linux-x86_64.sh -b -p $HOME/anaconda")
            sudo("echo '\n\nAdded for anaconda path' >> $HOME/.bashrc")
            sudo("echo 'export PATH=\"$HOME/anaconda/bin:$PATH\"' >> $HOME/.bashrc")
            sudo("source ~/.bashrc")


@task
def install_coco_api():
    '''
    Install coco api
    '''
    with cd('/home/azureuser'):
        if not exists("/home/azureuser/coco/"):
            sudo('git clone https://github.com/pdollar/coco.git')
        with cd('coco/PythonAPI'):
            sudo('/home/azureuser/anaconda/bin/python setup.py build_ext install')


@task
def set_permissions_on_codalab_temp():
    '''
    Set proper permissions on compute workers.
    '''
    with settings(warn_only=True):
        sudo("bindfs -o perms=0777 /codalabtemp /codalabtemp")


@task
def update_compute_worker():
    run('cd codalab-competitions && git checkout . && git pull --rebase')
    with settings(warn_only=True):
        sudo("stop codalab-compute-worker")
        sudo("stop codalab-monitor")
        sudo("start codalab-compute-worker")
        sudo("start codalab-monitor")


@task
def update_conda():
    with settings(warn_only=True):
        if not run('conda'):
            # If we can't run conda add it to the path
            run('echo "export PATH=~/anaconda/bin:$PATH" >> ~/.bashrc')
    run('conda update --yes --prefix /home/azureuser/anaconda anaconda')


@task
def setup_compute_worker_permissions():
    # Make the /codalabtemp/ files readable
    sudo("apt-get install bindfs")
    if not exists("/codalabtemp"):
        sudo("mkdir /codalabtemp")
    set_permissions_on_codalab_temp()

    # Make private stuff private
    sudo("chown -R azureuser:azureuser ~/codalab-competitions")
    sudo("chmod -R 700 ~/codalab-competitions")
    sudo("chown azureuser:azureuser ~/.codalabconfig")
    sudo("chmod 700 ~/.codalabconfig")


# OTHER UTILITIES SUCH AS MYSQL DUMP, etc
@roles('web')
@task
def get_database_dump():
    '''Saves backups to $CODALAB_MYSQL_BACKUP_DIR/launchdump-year-month-day-hour-min-second.sql.gz'''
    require('configuration')
    configuration = DeploymentConfig(env.cfg_label, env.cfg_path)
    db_host = "localhost"
    db_name = configuration.getDatabaseName()
    db_user = configuration.getDatabaseUser()
    db_password = configuration.getDatabasePassword()

    import time
    timestr = time.strftime("%Y%m%d-%H%M%S")
    dump_file_name = '{}-{}-competitiondump.sql.gz'.format(env.cfg_label, timestr)

    run('mysqldump --host=%s --user=%s --password=%s %s --port=3306 | gzip > /tmp/%s' % (
        db_host,
        db_user,
        db_password,
        db_name,
        dump_file_name)
        )
    backup_directory = os.path.dirname(os.path.realpath(__file__))

    get('/tmp/%s' % dump_file_name, backup_directory)


@roles('web')
@task
def put_mysql_dump_to_new_database():
    '''Puts dubmped database to new location'''
    require('configuration')
    configuration = DeploymentConfig(env.cfg_label, env.cfg_path)
    db_host = "localhost"
    db_database = configuration.getDatabaseName()
    db_user = configuration.getDatabaseUser()
    db_password = configuration.getDatabasePassword()

    backup_directory = os.path.dirname(os.path.realpath(__file__))

    put(local_path='{}/competitiondump.sql.gz'.format(backup_directory),
        remote_path='/home/azureuser/db_dump.sql.gz',
        use_sudo=True)

    # with cd('$HOME'):
    #     run('gunzip db_dump.sql.gz')
    #     run('mysql -u %s -p %s -h %s %s < db_dump.sql' % (
    #         db_user,
    #         db_password,
    #         db_host,
    #         db_database)
    #         )


@task
def install_packages_compute_workers():
    # --yes and --force-yes accepts the Y/N question when installing the package
    sudo('apt-get update')
    sudo('apt-get --yes --force-yes install libsm6 openjdk-7-jre')
    sudo('apt-get --yes --force-yes install r-base')
    sudo('apt-get --yes --force-yes --fix-missing install mono-runtime libmono-system-web-extensions4.0-cil libmono-system-io-compression4.0-cil')

    # check for khiops dir if not, put
    if not exists("/home/azureuser/khiops/"):
        run('mkdir -p /home/azureuser/khiops/')
        put("~/khiops/", "/home/azureuser/") # actually ends up in /home/azureuser/khiops
        sudo("chmod +x /home/azureuser/khiops/bin/64/MODL")


@task
def khiops_print_machine_name_and_id():
    sudo("chmod +x /home/azureuser/khiops/bin/64/MODL")
    sudo("chmod +x /home/azureuser/khiops/get_license_info.sh")
    with cd('/home/azureuser/khiops/'):
        run("./get_license_info.sh")

