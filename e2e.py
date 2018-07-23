import os
import subprocess
import argparse
from time import sleep
from colorama import Fore, Style, init
#argparse
parser = argparse.ArgumentParser(description='receive directory input for e2e testing')
parser.add_argument('dir',type=str,metavar='DIR',\
	help='specify the directory where your polyswarm repos lie, eg ~/ps, $(pwd)')
args = parser.parse_args()
init()
#globals
ab_path = os.path.abspath(args.dir)
PS_GITHUB_URL = 'https://github.com/polyswarm/'
PS_REPOS  = ["polyswarmd", "ambassador", "arbiter", "contracts", "priv-testnet", "microengine","orchestration"]
ALL_REPOS = ["polyswarmd", "ambassador", "arbiter", "contracts", "priv-testnet", "microengine","orchestration"]
stars='***********************************'

def dock_clean():
	cleancmd = 'docker container prune -f'
	clean2 =  'docker image prune -f'
	subprocess.run(cleancmd.split())
	subprocess.run(clean2.split())

print(Fore.MAGENTA+"your polyswarm repos lie in: " + ab_path)
#enum files in specified dir, check em and pop what they got
for filename in os.listdir(ab_path):
	if os.path.isdir(os.path.join(ab_path,filename)):
		for repo in PS_REPOS:
			if (filename == repo):
				PS_REPOS.remove(repo)


#if they don't have everything
if (PS_REPOS):

	print('Detected some repos, but here\'s what you need:')
	print(str(PS_REPOS)+Style.RESET_ALL)
	sleep(2)
	os.chdir(ab_path)
	command = 'git clone -b master {0}{1}'.format(PS_GITHUB_URL,repo)

	for repo in PS_REPOS:
		subprocess.run(command.split())
		print(Fore.MAGENTA+"cloned master branch of " + repo)
		print(stars+"\nbuilding image from cloned repo...\n"+stars+Style.RESET_ALL)
		sleep(2)
		os.chdir(os.path.join(ab_path,repo))
		command2 = 'docker build -t polyswarm/{0} -f docker/Dockerfile .'.format(repo)
		subprocess.run(command2.split())
#if they got everything
else:
	print(Fore.MAGENTA+"You have all of our necessary repos in your specified directory,\
 please make sure they're up to date :)")
	sleep(3)


#build remaining repos
print("downloaded and built these repos: " + str(PS_REPOS))
ALL_REPOS.remove('orchestration')
TO_BUILD = list(set(ALL_REPOS) - set(PS_REPOS))
print("repos to build: "+str(TO_BUILD) + Style.RESET_ALL)
sleep(2)
for repo in TO_BUILD:
	os.chdir(os.path.join(ab_path,repo))
	cmd = 'docker build -t polyswarm/{0} -f docker/Dockerfile .'.format(repo)
	subprocess.run(cmd.split())
dock_clean()

def compose_test():
	print(Fore.MAGENTA+"beginning testing..." + Style.RESET_ALL)
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
			print(Fore.MAGENTA+"testing "+Fore.GREEN+proj+Fore.MAGENTA+" success :)")
		else:
			print(Fore.MAGENTA+"testing "+Fore.GREEN+proj+Fore.RED+" failed :(")
		print(Style.RESET_ALL)

compose_test()