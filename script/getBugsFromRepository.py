import os
import shutil 
import subprocess
import json

REPOSITORIES_PATH = os.path.join(os.path.dirname(__file__), "..", "repositories")
BUGS_PATH = os.path.join(os.path.dirname(__file__), "..", "bugs")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data")


def get_bug_branches(project_path):
	branches = []
	cmd = "cd %s; git branch -a" % project_path
	output = subprocess.check_output(cmd, shell=True)
	for line in output.split():
		if "bugs-dot-jar_" in line:
			branches+= [line]
	return branches


def extract_bug_id(branch):
	tmp = branch[branch.index("_") + 1::]
	tmp = tmp[tmp.index("-") + 1::]
	return tmp.split("_")


def create_bug(project_path, branch_name, destination):
	cmd = "cd %s; git checkout %s;" % (project_path, branch_name)
	subprocess.call(cmd, shell=True)
	shutil.copytree(project_path, destination)
	shutil.rmtree(os.path.join(destination, ".git"))

def get_human_patch(bug_path):
	diff_patch = os.path.join(bug_path, ".bugs-dot-jar", "developer-patch.diff")
	with open(diff_patch) as fd:
		return fd.read()

def get_failing_tests(bug_path):
	tests = []
	diff_patch = os.path.join(bug_path, ".bugs-dot-jar", "test-results.txt")
	with open(diff_patch) as fd:
		maven_log = fd.read()
		if "Results :" not in maven_log:
			print bug_path
			return tests, total, failure, error, skipped
		index = maven_log.index("Results :") + 10
		for line in maven_log[index::].split("\n"):
			line = line.replace("Failed tests: ", "").replace("Tests in error: ", "").strip()
			if line == '':
				continue
			if "Tests run:" in line:
				total_start = line.index(": ") + 2
				total_end = line.index(",")

				failure_start = line.index(": ", total_start) + 2
				failure_end = line.index(",", failure_start)

				error_start = line.index(": ", failure_end) + 2
				error_end = line.index(",", error_start)

				skipped_start = line.index(": ", error_end) + 2
				skipped_end = len(line)
				if "," in line[skipped_start::]:
					skipped_end = line.index(", ", skipped_start)


				total = int(line[total_start:total_end])
				failure = int(line[failure_start:failure_end])
				error = int(line[error_start:error_end])
				skipped = int(line[skipped_start::skipped_end])


				break
			tests += [line]
	return tests, total, failure, error, skipped

for project_name in os.listdir(REPOSITORIES_PATH):
	
	project_path = os.path.join(REPOSITORIES_PATH, project_name)
	bug_project_path = os.path.join(BUGS_PATH, project_name)
	project_data_path = os.path.join(DATA_PATH, project_name)

	if not os.path.exists(project_path):
		os.makedirs(project_path)

	if not os.path.exists(bug_project_path):
		os.makedirs(bug_project_path)

	if not os.path.exists(project_data_path):
		os.makedirs(project_data_path)

	branches = get_bug_branches(project_path)
	for branch in branches:
		(jira_id, fix_commit) = extract_bug_id(branch)
		bug_path = os.path.join(bug_project_path, jira_id)
		bug_data_path = os.path.join(project_data_path, jira_id + ".json")

		if os.path.exists(bug_path):
			continue

		bug = {
			"project": project_name,
			"id": jira_id,
			"fix_commit": fix_commit,
		}

		create_bug(project_path, branch, bug_path)

		# human patch
		bug['patch'] = get_human_patch(bug_path)
		bug['files'] = bug['patch'].count("+++ b/")
		bug['linesAdd'] = bug['patch'].count("\n+ ")
		bug['linesRem'] = bug['patch'].count("\n- ")
		

		# failing tests
		(tests, total, failure, error, skipped) = get_failing_tests(bug_path)
		bug['failing_tests'] = tests
		bug['nb_test'] = total
		bug['nb_failure'] = failure
		bug['nb_error'] = error
		bug['nb_skipped'] = skipped

		with open(bug_data_path, 'w') as fd:
			json.dump(bug, fd)
		

