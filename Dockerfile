FROM odoo:19.0

USER root

RUN pip3 install --no-cache-dir --break-system-packages \
    openupgradelib==3.13.7 \
    cachetools

USER odoo
