'''
Copyright 2023 by Theodore Jones tjones2@fastmail.com 

This code is licensed under the The Parity Public License 7.0.0

As far as the law allows, this software comes as is, without any 
warranty or condition, and the contributor won't be liable to anyone
for any damages related to this software or this license, 
under any kind of legal claim.
'''

import os
import random
import string
import subprocess

# Function to generate random password for MySQL wordpress user
def generate_password(length=10):
    all_chars = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(all_chars) for i in range(length))
    return password

# Generate a random password for the MySQL root user
mysql_root_password = generate_password()

# Generate a random password for the WordPress database user
wordpress_db_password = generate_password()

# Environment setup
subprocess.call('mkdir /var/www/etc', shell=True)

# Copy the system's resolv.conf file to enable DNS resolution in the chroot
subprocess.call('cp /etc/resolv.conf /var/www/etc/resolv.conf', shell=True)

# Package installation
subprocess.call('pkg_add php-8.2.6 php-cgi-8.2.6 fcgi php-curl-8.2.6 php-intl-8.2.6  php-mysqli-8.2.6 php-gd-8.2.6 pecl82-imagick-3.7.0p1 php-zip-8.2.6 mariadb-server mariadb-client', shell=True)
subprocess.call('pkg_add wget unzip-6.0p16', shell=True)

# PHP config
subprocess.call('cp /usr/local/share/examples/php-8.2/php.ini-production /usr/local/share/php-8.2/php.ini', shell=True)

subprocess.call('cp /etc/php-8.2.sample/*.ini /etc/php-8.2', shell=True)


# Create a PHP-FPM pool configuration
with open('/etc/php-fpm.d/www.conf', 'w') as f:
    f.write('[www]\n')
    f.write('user = www\n')
    f.write('group = www\n')
    f.write('listen = /var/www/run/php-fpm.sock\n')
    f.write('listen.owner = www\n')
    f.write('listen.group = www\n')
    f.write('listen.mode = 0660\n')
    f.write('pm = dynamic\n')
    f.write('pm.max_children = 50\n')
    f.write('pm.start_servers = 5\n')
    f.write('pm.min_spare_servers = 5\n')
    f.write('pm.max_spare_servers = 35\n')
    f.write('chroot = /var/www\n')

# Start and enable PHP-FPM service
subprocess.call('rcctl start php82_fpm', shell=True)
subprocess.call('rcctl enable php82_fpm', shell=True)

# HTTPD configuration
with open('/etc/httpd.conf', 'w') as f:
    f.write('types { include "/usr/share/misc/mime.types" }\n')
    f.write('server "default" {\n')
    f.write('    listen on egress port 80\n')
    f.write('    root "/wordpress"\n')
    f.write('    directory index index.php\n')
    f.write('    location "*.php*" {\n')
    f.write('            fastcgi socket "/run/php-fpm.sock"\n')
    f.write('    }\n')
    f.write('}\n')

# Start and enable HTTPD service
subprocess.call('rcctl start httpd', shell=True)
subprocess.call('rcctl enable httpd', shell=True)

# MySQL configuration

# Update MySQL configuration file with new root password
with open('/etc/my.cnf', 'a') as my_cnf:
    my_cnf.write('\n[client]\n')
    my_cnf.write('user            = root\n')
    my_cnf.write('password        = ' + mysql_root_password + '\n')
    my_cnf.write('port            = 3306\n')
    my_cnf.write('socket          = /var/run/mysql/mysql.sock\n')

subprocess.call('mysql_install_db', shell=True)
subprocess.call('rcctl start mysqld', shell=True)

subprocess.call('rcctl enable mysqld', shell=True)

# Download and configure Wordpress
subprocess.call('wget https://wordpress.org/latest.zip -P /tmp', shell=True)
subprocess.call('unzip /tmp/latest.zip -d /var/www', shell=True)
subprocess.call('chown -R www:www /var/www/wordpress', shell=True)

# Create the WordPress database
mysql_commands = f"""
    CREATE DATABASE wordpress;
    CREATE USER 'wordpress'@'localhost' IDENTIFIED BY '{wordpress_db_password}';
    GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'localhost';
    FLUSH PRIVILEGES;
"""

# Execute the MySQL commands
subprocess.Popen(['mysql', '-u', 'root', '-p' + mysql_root_password, '-e', mysql_commands])

# Copy the WordPress configuration file and update the database settings
# Copy the WordPress configuration file
subprocess.call('cp /var/www/wordpress/wp-config-sample.php /var/www/wordpress/wp-config.php', shell=True)

# Update the database settings using sed
subprocess.call(f'sed -i -e "s/database_name_here/wordpress/g" -e "s/username_here/wordpress/g" -e "s/password_here/{wordpress_db_password}/g" -e "s/localhost/127.0.0.1/g" /var/www/wordpress/wp-config.php', shell=True)

# Start and enable PHP-FPM service
subprocess.call('rcctl start php82_fpm', shell=True)
subprocess.call('rcctl enable php82_fpm', shell=True)

# Start and enable HTTPD service
subprocess.call('rcctl start httpd', shell=True)
subprocess.call('rcctl enable httpd', shell=True)

# Start and enable MySQL service
subprocess.call('rcctl start mysqld', shell=True)
subprocess.call('rcctl enable mysqld', shell=True)
