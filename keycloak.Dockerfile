# Dockerfile for Keycloak with custom theme
FROM quay.io/keycloak/keycloak:24.0.0

# Copy custom theme
COPY ./aura-ai-theme /opt/keycloak/themes/aura-ai-theme

# Optional: Add any custom provider JARs if you have them
# COPY ./providers/*.jar /opt/keycloak/providers/

# Keycloak build for optimized startup
RUN /opt/keycloak/bin/kc.sh build
