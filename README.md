# 🌀 One-Command WordPress Installer for Ubuntu

A fully automated Bash script (written in Python) to set up a ready-to-use WordPress website on an Ubuntu server. This script handles everything from installing necessary packages, setting up MySQL, enabling Apache modules, downloading WordPress, and optionally configuring SSL via Let's Encrypt.

## 🚀 Features

- Installs Apache, MySQL/MariaDB, PHP, and WordPress
- Optional domain configuration with Apache VirtualHost
- Automatic SSL setup using Let's Encrypt and Certbot
- Configures MySQL database and user for WordPress
- Automatically sets correct permissions
- Clean and interactive setup

---

## ⚙️ Requirements

- Ubuntu/Debian-based Linux system
- Root privileges (`sudo` access)

---

## 🧰 Packages Installed

- Apache2
- MySQL Server
- PHP and essential modules
- Certbot (optional for SSL)
- WordPress

---

## 🛠️ Usage

1. Clone the repo:
    ```bash
    git clone https://github.com/sudharshnatr1/Wordpress-setup.git
    cd Wordpress-setup
    ```
2. Run the script with root privileges:
    ```bash
    sudo python3 wordpress_setup.py
    ```

4. Follow the interactive prompts:
   - Enter domain (or leave blank for localhost)
   - Choose whether to install SSL
   - Configure database info (user/pass auto-generated if you want)

---

## 🌐 Access Your Site

- **Without a domain:** http://localhost (or your server's IP)
- **With domain and SSL:** https://yourdomain.com

---

