#!/bin/bash
cat > /tmp/maint-off.sql <<'SQL'
INSERT INTO app_settings (key, value, updated_at) VALUES ('site.maintenance','false', now())
  ON CONFLICT (key) DO UPDATE SET value='false', updated_at=now();
SQL
sudo docker exec -i harness-db psql -U harness -d harness < /tmp/maint-off.sql
echo CLOSED
