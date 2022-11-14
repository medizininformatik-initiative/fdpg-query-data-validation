#!/bin/bash
docker-compose -p PROJECT_CONTEXT down -f docker-compose-validation.yml
docker-compose -p PROJECT_CONTEXT down -f docker-compose-vms.yml
echo "Shutdown finished"