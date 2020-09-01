#!/usr/bin/python

import yaml

with open('data.yaml','r') as yamlfile:
    cur_yaml = yaml.safe_load(yamlfile) # Note the safe_load
    cur_yaml['bugs_tree'].update(new_yaml_data_dict)

if cur_yaml:
    with open('data.yaml','w') as yamlfile:
        yaml.safe_dump(cur_yaml, yamlfile) # Also note the safe_dump