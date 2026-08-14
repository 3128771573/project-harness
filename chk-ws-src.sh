#!/bin/bash
sudo docker exec harness-backend python -c "import sys; sys.path.insert(0, '/app/backend'); from app.routers import im; import inspect; print(inspect.getsource(im.im_ws))" 2>&1 | head -40
