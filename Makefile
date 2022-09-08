coverage: ## check code coverage
	coverage run --source terra_sdk -m pytest
	coverage report -m
	poetry run coverage html
	# $(BROWSER) htmlcov/index.html


clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

test-unit: ## runs tests
	python3.9 -m unittest test/unit/test_all.py

test-int: ## runs 
	$(info "******** INTEGRATION TEST ********")
	python3.9  ./test/integration/test_dca.py

test-int2: local_terra_run test-int local_terra_rm

local_terra_run: 
	cd test/integration/localterra/; local_terra_image.sh run
#   we need to wait for the blochain to start producing blocks.
#   If some tests failed, increase the sleep time!
	sleep 35
	

local_terra_rm:
	cd test/integration/localterra/; local_terra_image.sh rm

#example: make local_terra cmd=help
local_terra :
	cd test/integration/localterra/; local_terra_image.sh $(cmd)


