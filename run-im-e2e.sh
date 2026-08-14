#!/bin/bash
set -e
KEY=/home/x230user/.ssh/id_ed25519_cloud
scp -i $KEY -o StrictHostKeyChecking=accept-new /home/x230user/projects/harness/test_im_e2e.py ubuntu@124.222.140.57:/tmp/test_im_e2e.py
ssh -i $KEY -o StrictHostKeyChecking=accept-new ubuntu@124.222.140.57 'sudo docker exec -i harness-backend python < /tmp/test_im_e2e.py'
