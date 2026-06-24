#!/bin/bash
# Initialisation du certificat Let's Encrypt (à lancer une seule fois sur le serveur).
# Inspiré de https://github.com/wmnnd/nginx-certbot
set -e

DOMAIN="stac-wiw.kbaddour.fr"
EMAIL="baddour.khalil@gmail.com"
DATA_PATH="./certbot"
STAGING=0   # Mettre à 1 pour tester (évite les rate-limits Let's Encrypt)

# ── Paramètres TLS recommandés ─────────────────────────────────────────────
if [ ! -e "$DATA_PATH/conf/options-ssl-nginx.conf" ] || \
   [ ! -e "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
    echo ">>> Téléchargement des paramètres TLS recommandés…"
    mkdir -p "$DATA_PATH/conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
        > "$DATA_PATH/conf/options-ssl-nginx.conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem \
        > "$DATA_PATH/conf/ssl-dhparams.pem"
fi

# ── Certificat factice pour démarrer nginx ────────────────────────────────
echo ">>> Création d'un certificat auto-signé temporaire pour $DOMAIN…"
mkdir -p "$DATA_PATH/conf/live/$DOMAIN"

docker compose run --rm --entrypoint "openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
    -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
    -out    /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
    -subj   '/CN=localhost'" certbot

echo ">>> Démarrage de nginx avec le certificat temporaire…"
docker compose up --force-recreate -d nginx

# ── Remplacement par le vrai certificat ───────────────────────────────────
echo ">>> Suppression du certificat temporaire…"
docker compose run --rm --entrypoint "sh -c '\
    rm -rf /etc/letsencrypt/live/$DOMAIN && \
    rm -rf /etc/letsencrypt/archive/$DOMAIN && \
    rm -rf /etc/letsencrypt/renewal/$DOMAIN.conf'" certbot

echo ">>> Demande du certificat Let's Encrypt pour $DOMAIN…"
STAGING_ARG=""
if [ "$STAGING" = "1" ]; then
    STAGING_ARG="--staging"
fi

docker compose run --rm --entrypoint "certbot certonly --webroot \
    -w /var/www/certbot \
    $STAGING_ARG \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN" certbot

echo ">>> Rechargement de nginx avec le vrai certificat…"
docker compose exec nginx nginx -s reload

echo ""
echo "✓ Terminé ! Le site est disponible sur https://$DOMAIN"
