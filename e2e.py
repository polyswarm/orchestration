import os
import subprocess
import argparse
from time import sleep
from colorama import Fore, Style, init
import timeit
import logging
start_time = timeit.default_timer()
logging.basicConfig(level=logging.INFO)
#argparse
parser = argparse.ArgumentParser(description='receive directory input for e2e testing')
parser.add_argument('dir',type=str,metavar='DIR',\
	help='specify the directory where your polyswarm repos lie, ex: ~/ps, $(pwd)')
parser.add_argument('--testing',metavar='FALSE', help="flag to remove dead docker containers")
args = parser.parse_args()
init()
#globals
ab_path = os.path.abspath(args.dir)
PS_GITHUB_URL = 'https://github.com/polyswarm/'
PS_REPOS  = ["polyswarmd", "ambassador", "arbiter", "contracts", "priv-testnet", "microengine","orchestration", "relay"]
ALL_REPOS = ["polyswarmd", "ambassador", "arbiter", "contracts", "priv-testnet", "microengine","orchestration", "relay"]
stars='***********************************'

def discover_ps_repos():
	logging.info(Fore.MAGENTA+"your polyswarm repos lie in: " + ab_path)
	#enum files in specified dir, check em and pop what they got
	for filename in os.listdir(ab_path):
		if os.path.isdir(os.path.join(ab_path,filename)):
			for repo in PS_REPOS:
				if (filename == repo):
					PS_REPOS.remove(repo)

def acquire_remaining_repos():
	#if they don't have everything
	if (PS_REPOS):
		logging.info('Detected some repos, but here\'s what you need:')
		logging.info(str(PS_REPOS)+Style.RESET_ALL)
		if args.testing:
			sleep(2)

		for repo in PS_REPOS:
			os.chdir(ab_path)
			command = 'git clone -b master {0}{1}'.format(PS_GITHUB_URL,repo)
			logging.info(command)
			subprocess.run(command.split(), check=True)
			if args.testing:
				sleep(3)
			logging.info(Fore.MAGENTA+"cloned master branch of " + repo)
			logging.info(stars+"\nbuilding image from cloned repo...\n"+stars+Style.RESET_ALL)
			if args.testing:
				sleep(2)
			os.chdir(os.path.join(ab_path,repo))
			command2 = 'docker build -q -t polyswarm/{0} -f docker/Dockerfile .'.format(repo)
			subprocess.run(command2.split())
	#if they got everything
	else:
		logging.info(Fore.MAGENTA+"You have all of our necessary repos in your specified directory, \
please make sure they're up to date :)")
		if args.testing:
			sleep(3)

def build_repos():
	#build remaining repos
	logging.info(Fore.MAGENTA+"downloaded and built these repos: " + Fore.GREEN+ str(PS_REPOS))
	ALL_REPOS.remove('orchestration')
	TO_BUILD = list(set(ALL_REPOS) - set(PS_REPOS))
	logging.info(Fore.MAGENTA+ "repos to build: "+Fore.GREEN+str(TO_BUILD) + Style.RESET_ALL)
	if args.testing:
		sleep(2)
	for repo in TO_BUILD:
		os.chdir(os.path.join(ab_path,repo))
		logging.info(Fore.MAGENTA+"building "+ Fore.GREEN+ str(repo)+Style.RESET_ALL)
		cmd = 'docker build -q -t polyswarm/{0} -f docker/Dockerfile .'.format(repo)
		subprocess.run(cmd.split())

def dock_clean():
	logging.info(Fore.MAGENTA + "Getting rid of dead containers and images for"+Fore.GREEN+" you")
	cleancmd = 'docker container prune -f'
	clean2 =  'docker image prune -f'
	subprocess.run(cleancmd.split())
	subprocess.run(clean2.split())

def compose_test():
	logging.info(Fore.MAGENTA+"Beginning testing...average test time on dev setup ~4 minutes" + Style.RESET_ALL)
	if args.testing:
		sleep(1)
	composecmd = 'docker-compose -f {0}/dev.yml -f {0}/test.yml up -d'.format(os.path.join(ab_path,'orchestration'))
	subprocess.run(composecmd.split())

	projs_to_check = ["contracts","arbiter","ambassador","microengine"]

	for proj in projs_to_check:
		id_cmd = 'docker-compose -f {1}/dev.yml -f {1}/test.yml ps -q {0}'.format(proj,os.path.join(ab_path,'orchestration'))
		c_id = subprocess.check_output(id_cmd.split()).decode('ASCII')

		ret_cmd = 'docker wait {0}'.format(c_id)
		retval_proj = subprocess.check_output(ret_cmd.split()).decode('ASCII')
		if retval_proj==str("0\n"):
			logging.info(Fore.MAGENTA+"testing "+Fore.GREEN+proj+Fore.MAGENTA+" success :)")
		else:
			logging.info(Fore.MAGENTA+"testing "+Fore.GREEN+proj+Fore.RED+" failed :( with return value:" + retval_proj)
	logging.info(Style.RESET_ALL)

def decompose():
	cmd = 'docker-compose -f {0}/dev.yml -f {0}/test.yml down'.format(os.path.join(ab_path,'orchestration'))
	logging.info(Fore.MAGENTA+"decomposing..."+Style.RESET_ALL)
	subprocess.run(cmd.split())

decompose()
if args.testing:
	dock_clean()
discover_ps_repos()
acquire_remaining_repos()
build_repos()
if args.testing:
	dock_clean()
compose_test()
decompose()
stop_time = timeit.default_timer()
tot = stop_time - start_time
logging.info("completed in: "+Fore.RED + str(round(tot,3))+Fore.GREEN + " seconds :)"+Style.RESET_ALL)