# Load .env if it exists
ifneq (,$(wildcard .env))
    include .env
    export $(shell sed 's/=.*//' .env)
endif

make run-flask:
	export AWS_PROFILE=$(AWS_PROFILE_NAME)
	export AWS_REGION=$(AWS_REGION)
	flask --app src/api/main.py --debug run