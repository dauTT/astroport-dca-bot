SHELL=/bin/bash

PWD=$(shell pwd)
clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +



install_python:
	sudo apt install python3.9-venv

venv:
	python3.9 -m venv "$(PWD)/venv/"

install_requirements:
	( source  "$(PWD)/venv/bin/activate" ;\
	  pip install -r requirements.txt;\
	)
	 
install: install_python venv install_requirements

test-unit:
	python3.9 test/unit/test_all.py

test-int-exec-order: local_terra_run test-exec-order  local_terra_rm
test-int-dca: local_terra_run test-dca  local_terra_rm

# Defining "test-int: test-int-exec-order test-int-dca" does not work.
# therefore we need to do a workaround: 
test-int: 
	$(MAKE) test-int-dca    
	$(MAKE) test-int-exec-order

test: test-unit test-int

# Make sure to run first "make local_terra_run" before executing the following cmd
test-dca: 
	@echo "******* test_exec_dca *******"
	python  "$(PWD)/test/integration/test_dca.py"

# Make sure to run first "make local_terra_run" before executing the following cmd
test-exec-order:  
	@echo "******* test_exec_order *******"
	python  "$(PWD)/test/integration/test_exec_order.py"

local_terra_run: 
	@echo "local_terra_run"
	cd "$(PWD)/test/integration/localterra" ; local_terra_image.sh run
#   we need to wait for the blochain to start producing blocks.
#   If some tests failed, increase the sleep time!
	sleep 35
	
local_terra_rm:
	@echo "local_terra_rm"
	cd "$(PWD)/test/integration/localterra"; local_terra_image.sh rm
	

#example: make local_terra cmd=help
local_terra :
	cd "$(PWD)/test/integration/localterra"; local_terra_image.sh $(cmd)
