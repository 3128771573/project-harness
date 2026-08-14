#!/bin/bash
set -e
scp -i /home/x230user/.ssh/id_ed25519_cloud /tmp/clean-diag.sh ubuntu@124.222.140.57:/tmp/
scp -i /home/x230user/.ssh/id_ed25519_cloud /tmp/verify-p1-live.sh ubuntu@124.222.140.57:/tmp/
ssh -i /home/x230user/.ssh/id_ed25519_cloud ubuntu@124.222.140.57 'bash /tmp/clean-diag.sh && bash /tmp/verify-p1-live.sh'
