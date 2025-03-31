import os
import sys
import subprocess
import secrets
#root previlages checker
if os.geteuid() != 0:
    print("script must be run as root. Please run it with sudo or as root.")
    sys.exit(1)

domain = input("Enter domain name for WordPress site or just enter to levae bank: ").strip()
use_ssl = False
email = None
if domain:
    domain = domain.lower()
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = domain.split("://")[1]
    domain = domain.rstrip("/")

    choice = input(f"Do you want to obtain a Let's Encrypt SSL certificate for {domain}? [y/N]: ").strip().lower()
    if choice == 'y' or choice == 'yes':
        use_ssl = True
        email = input("Enter email for Let's Encrypt registration (leave blank to skip email): ").strip()
        if email == "":
            email = None

packages = [
    "apache2", 
    "mysql-server", 
    "php", 
    "libapache2-mod-php", 
    "php-mysql",
    "php-curl", 
    "php-gd", 
    "php-xml", 
    "php-mbstring",
    "wget",   
]
if use_ssl:
    packages += ["certbot", "python3-certbot-apache"]

os.environ["DEBIAN_FRONTEND"] = "noninteractive"

try:
    print("Updating package list...")
    subprocess.run(["apt-get", "update"], check=True)
    print("Installing required packages: " + " ".join(packages) + " ...")
    subprocess.run(["apt-get", "install", "-y"] + packages, check=True)
except subprocess.CalledProcessError as errorr :
    print(f"Error: Package installation failed {errorr}.")
    sys.exit(1)

try:
    subprocess.run(["systemctl", "enable", "--now", "apache2"], check=True)
except subprocess.CalledProcessError:
    print("Could not enable/start apache2 service (it may not be supported on this system).")
try:
    subprocess.run(["systemctl", "enable", "--now", "mysql"], check=True)
except subprocess.CalledProcessError:
    try:
        subprocess.run(["systemctl", "enable", "--now", "mariadb"], check=True)
    except subprocess.CalledProcessError:
        print("Could not enable/start MySQL service (please ensure MySQL/MariaDB is running).")
mysqlinstall=input("do you to install mysql  [y/N]").strip().lower()
if mysqlinstall == 'y' or mysqlinstall == 'yes':
    db_name = input("enter a database name (Do not use any special characters)").lower()
    db_user = input("enter a name database user (Do not use any special characters)").lower()
    passwd=input("do you to create a password  [y/N]").strip().lower()
    if passwd == 'y' or passwd == 'yes':
        db_pass = input("enter your password")
    else:
        db_pass = secrets.token_urlsafe(16).rstrip('=')
    sql_commands = (
        f"CREATE DATABASE IF NOT EXISTS {db_name}; "
        f"CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_pass}'; "
        f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'localhost'; "
        "FLUSH PRIVILEGES;"
    )
    try:
        subprocess.run(["mysql", "-u", "root", "-e", sql_commands], check=True)
    except subprocess.CalledProcessError:
        print("Error: MySQL database setup failed. Please check MySQL status and root credentials.")
        sys.exit(1)

print("Downloading WordPress...")
wp_tar = "/tmp/wordpress.tar.gz"
wp_download_url = "https://wordpress.org/latest.tar.gz"
try:
    subprocess.run(["wget", "-q", "-O", wp_tar, wp_download_url], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error: Failed to download WordPress ({e}).")
    sys.exit(1)
default_index = "/var/www/html/index.html"
if os.path.exists(default_index):
    os.remove(default_index)

try:
    subprocess.run(["tar", "-xzf", wp_tar, "-C", "/tmp"], check=True)
    subprocess.run(["cp", "-a", "/tmp/wordpress/.", "/var/www/html/"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error: Failed to extract or copy WordPress files ({e}).")
    sys.exit(1)
subprocess.run(["chown", "-R", "www-data:www-data", "/var/www/html"], check=False)

try:
    subprocess.run(["a2enmod", "rewrite"], check=True)
except subprocess.CalledProcessError:
    print("Failed to enable Apache rewrite module. You may need to enable it manually.")
if domain:
    vhost_file = f"/etc/apache2/sites-available/{domain}.conf"
    vhost_config = f"""<VirtualHost *:80>
    ServerName {domain}
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html

    ErrorLog ${{APACHE_LOG_DIR}}/error.log
    CustomLog ${{APACHE_LOG_DIR}}/access.log combined

    <Directory /var/www/html>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
"""

    try:
        with open(vhost_file, "w") as f:
            f.write(vhost_config)
    except Exception as exep:
        print(f"Error: Could not write Apache vhost file ({exep}).")
        sys.exit(1)
    try:
        subprocess.run(["a2ensite", f"{domain}.conf"], check=True)
    except subprocess.CalledProcessError as errorr:
        print(f"Error: Failed to enable site configuration ({errorr}).")
        sys.exit(1)
else:
    apache_conf = "/etc/apache2/apache2.conf"
    try:
        
        with open(apache_conf, "r") as f:
            conf_text = f.read()
       
        new_conf_text = conf_text
        start = new_conf_text.find("<Directory /var/www/")
        if start != -1:
            end = new_conf_text.find("</Directory>", start)
            if end != -1:
                directory_block = new_conf_text[start:end]
                if "AllowOverride None" in directory_block:
                    new_block = directory_block.replace("AllowOverride None", "AllowOverride All")
                    new_conf_text = new_conf_text[:start] + new_block + new_conf_text[end:]
        if new_conf_text != conf_text:
            with open(apache_conf, "w") as f:
                f.write(new_conf_text)
    except Exception as e:
        print(f"Failed to update Apache AllowOverride setting ({e}). Permalinks may not work until this is fixed.")

subprocess.run(["systemctl", "reload", "apache2"], check=False)

if domain and use_ssl:
    print(f"Obtaining Let's Encrypt SSL certificate for {domain}...")

    try:
        if email:
            subprocess.run([
                "certbot", "--apache",
                "-d", domain,
                "--email", email,
                "--agree-tos", "--no-eff-email",
                "--redirect", "-n"
            ], check=True)
        else:
            subprocess.run([
                "certbot", "--apache",
                "-d", domain,
                "--agree-tos", "--register-unsafely-without-email",
                "--redirect", "-n"
            ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"SSL certificate setup failed ({e}). You can run Certbot manually later.")

subprocess.run(["systemctl", "reload", "apache2"], check=False)

# Output installation details and next steps
print("\n** WordPress installation script completed **")
if domain:
    site_url = f"http://{domain}"
else:
    site_url = "http://localhost (or your server's IP address)"
print(f"- WordPress files have been placed in /var/www/html")
print(f"- Apache is configured to serve the site at {site_url}")
if domain and use_ssl:
    print(f"- An SSL certificate has been installed. Visit https://{domain} to verify the HTTPS connection.")
if mysqlinstall == 'y' or mysqlinstall == 'yes':
    print("- A MySQL database and user for WordPress have been created:")
    print(f"        Database Name: {db_name}")
    print(f"        Database User: {db_user}")
    print(f"    Database Password: {db_pass}")
print("\nNext steps:")
print(f"1. In your web browser, visit {site_url} to run the WordPress setup wizard.")
print("2. When prompted, enter the database name, user, and password shown above.")
print("3. Complete the on-screen instructions to finish the WordPress installation.")
print("4. (Optional) After installation, log into the WordPress dashboard to configure settings, install plugins, etc.")
