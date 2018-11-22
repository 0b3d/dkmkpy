sudo docker exec -it $(sudo docker ps -aqf "ancestor=dkmkpy_renderer") /bin/bash
sudo docker exec -it $(sudo docker ps -aqf "ancestor=dkmkpy_postgis") /bin/bash
