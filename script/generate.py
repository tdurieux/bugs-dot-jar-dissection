import os
import json

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data")

bugs = []
for project_name in os.listdir(DATA_PATH):
  project_path = os.path.join(DATA_PATH, project_name)
  if not os.path.isdir(project_path):
    continue
  for bug_id in os.listdir(project_path):
    with open(os.path.join(project_path, bug_id)) as fd:
      bug = json.load(fd)
      bug['project'] = project_name
      bug['files'] = bug['patch'].count("+++ b/")
      bug['linesAdd'] = bug['patch'].count("\n+") - bug['files']
      bug['linesRem'] = bug['patch'].count("\n-") - bug['files']
      bug['singleLine'] = (bug['linesAdd'] == 1 and bug['linesRem'] == 0) or (bug['linesAdd'] == 0 and bug['linesRem'] == 1)
      print bug['singleLine']
      bugs += [bug]

print "Processed %d bugs" % len(bugs)
with open(os.path.join(DATA_PATH, "..", "docs", "data", "bugs.json"), "w") as fd:
  json.dump(bugs, fd)