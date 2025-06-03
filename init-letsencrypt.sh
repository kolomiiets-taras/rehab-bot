#!/bin/bash

# Functions for extended logging
log_step() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - STEP: $1" | tee -a ssl-setup.log
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" | tee -a ssl-setup.log >&2
}

log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO: $1" | tee -a ssl-setup.log
}

# Main function
setup_ssl() {
    local domain="spina.in.ua"
    local email="dr.loktionov@gmail.com"
    local nginx_conf_dir="./nginx/conf"
    local nginx_temp_conf="${nginx_conf_dir}/${domain}.temp.conf"

    # Start a new log file
    echo "SSL CERTIFICATE SETUP - $(date)" > ssl-setup.log
    log_step "Starting SSL setup process for $domain"

    # Stop previous containers
    log_step "Stopping previous containers"
    docker compose down -v || true

    # Prepare certbot directories
    log_step "Creating and configuring certbot directories"
    mkdir -p ./certbot/www/.well-known/acme-challenge
    mkdir -p ./certbot/conf
    sudo chown -R $(whoami):$(whoami) ./certbot || true

    log_step "Removing previous certbot data"
    rm -rf ./certbot/conf/*
    rm -rf ./certbot/www/*

    # Create a test file to verify accessibility
    log_step "Creating test file to verify accessibility"
    echo "Test file for Let's Encrypt validation verification" > ./certbot/www/.well-known/acme-challenge/test.txt

    # Create temporary Nginx configuration only for HTTP validation
    log_step "Creating temporary HTTP Nginx configuration"
    cat > "$nginx_temp_conf" << EOF
server {
    listen 80;
    server_name $domain www.$domain;

    # For Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        allow all;
        try_files \$uri =404;
    }

    location / {
        return 200 "Server running in setup mode";
        add_header Content-Type text/plain;
    }
}
EOF

    # Launch temporary Nginx container with temporary configuration
    log_step "Launching temporary Nginx container with temporary configuration"
    docker compose -f docker-compose.yml -f - up -d --no-deps nginx <<EOF
services:
  nginx:
    volumes:
      - ${nginx_temp_conf}:/etc/nginx/conf.d/temp.conf:ro
EOF

    # Check Nginx accessibility
    log_step "Checking Nginx accessibility"
    sleep 5

    # Check local accessibility
    log_step "Checking local Nginx accessibility"
    curl -v http://localhost:80 2>&1 | tee -a ssl-setup.log

    # Check validation path accessibility
    log_step "Checking ACME validation path accessibility"
    curl -v http://$domain/.well-known/acme-challenge/test.txt 2>&1 | tee -a ssl-setup.log

    # Obtain certificates through Let's Encrypt
    log_step "Obtaining SSL certificates through Let's Encrypt"
    docker compose run --rm --entrypoint="certbot" certbot \
        certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $email \
        --agree-tos \
        --no-eff-email \
        --domain $domain \
        --domain www.$domain \
        --verbose \
        --force-renewal \
        --non-interactive 2>&1 | tee -a ssl-setup.log

    # Fix permissions for certificates
    log_step "Fixing permissions for generated certificates"
    sudo chown -R $(whoami):$(whoami) ./certbot/conf/ || true
    sleep 2

    # Check successful certificate acquisition
    if [ ! -d "./certbot/conf/live/$domain" ]; then
        log_error "Failed to obtain certificates. Check ssl-setup.log file for details"

        # Remove temporary files
        log_step "Removing temporary files"
        rm -rf "$nginx_temp_conf"

        exit 1
    fi

    log_step "Certificates successfully obtained"

    # Remove temporary configuration
    log_step "Removing temporary configuration"
    rm -rf "$nginx_temp_conf"

    # Launch all containers with SSL (using main configuration)
    log_step "Launching all containers with SSL enabled"
    docker compose down
    docker compose up -d --build

    # Check service functionality
    log_step "Checking service functionality"
    sleep 15

    if curl -k -s https://$domain > /dev/null; then
        log_step "HTTPS service successfully launched and accessible"
        log_info "Service available at https://$domain"
    else
        log_error "Failed to connect to HTTPS service. Checking containers..."
        docker compose ps
        docker compose logs nginx | tail -n 30
    fi

    log_step "SSL setup completed"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - RESULT: Service available at https://$domain"
}

# Launch main function
setup_ssl