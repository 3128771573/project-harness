#!/bin/bash
set -e
scp -i /home/x230user/.ssh/id_ed25519_cloud /home/x230user/projects/harness/test_guestbook_v2.py ubuntu@124.222.140.57:/tmp/test_guestbook_v2.py
ssh -i /home/x230user/.ssh/id_ed25519_cloud ubuntu@124.222.140.57 'sudo docker exec -i harness-backend python < /tmp/test_guestbook_v2.py'
