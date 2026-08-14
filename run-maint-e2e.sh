#!/bin/bash
set -e
scp -i /home/x230user/.ssh/id_ed25519_cloud /home/x230user/projects/harness/test_maintenance_e2e.py ubuntu@124.222.140.57:/tmp/test_maintenance_e2e.py
ssh -i /home/x230user/.ssh/id_ed25519_cloud ubuntu@124.222.140.57 'sudo docker exec -i harness-backend python < /tmp/test_maintenance_e2e.py'
