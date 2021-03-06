#!/usr/bin/python

from sys import version_info
from optparse import OptionParser
import os
from crif.utils import (options_from_file, deep_search_path)
from crif._version import __version__
import time
import getpass
import sys
import json
import shutil
from pyspin.spin import make_spin, Default


def file_handler_wrap(options):
  def file_handler(filepath):
    if os.path.isfile(filepath):
      contents = []
      with open(filepath, 'r') as fread:
        for line in fread.readlines():
          line = line.replace('{{projectname}}', options.projectname)\
          .replace('{{organizationname}}', options.organizationname)\
          .replace('{{prefix}}', options.prefix)\
          .replace('{{date}}', options.date)\
          .replace('{{author}}', options.author)
          contents.append(line)
      with open(filepath+'__w', 'w') as fwrite:
        fwrite.writelines(contents)
      os.chmod(filepath+'__w', os.stat(filepath).st_mode)
      os.remove(filepath)
      os.rename(filepath+'__w', filepath)
      pass
    if filepath.find('{{projectname}}') != -1:
      new_path = filepath.replace('{{projectname}}', options.projectname)
      os.rename(filepath, new_path)
      pass
  return file_handler

def get_input(input_msg, default=None):
  if version_info >= (3, 0):
    input_value = input(input_msg)
  else:
    input_value = raw_input(input_msg.encode('utf8')).decode('utf8')

  if input_value == '':
    return default
  return input_value

@make_spin(Default, 'Cloning template project...')
def clone_template_project(projectname):

  os.system("git clone https://github.com/epingwang/iOSFrameworkTemplate.git --quiet -b name-replace "+projectname)

@make_spin(Default, 'Editing template project...')
def edit_template_project(options):
  deep_search_path(options.projectname, file_handler_wrap(options), ['.git', '.DS_Store', '.xcuserdatad'])

@make_spin(Default, 'Generating Pods project...')
def install_pod_dependencies(projectname):
  os.chdir(projectname+'/'+projectname+'Demo')
  os.system('pod install --silent')
  os.chdir('../')

def edit_project_file(options, projectname):
  if options.dynamic:
    os.chdir(projectname)
    os.system('plutil -convert json '+projectname+'.xcodeproj/project.pbxproj -o project.json')
    with open('project.json', 'r') as framework_project_file:
      framework_project_obj = json.load(framework_project_file)
      root_id = framework_project_obj["rootObject"]
      objects = framework_project_obj["objects"]
      target_ids = objects[root_id]['targets']
      for target_id in target_ids:
        target = objects[target_id]
        build_conf_list = objects[target['buildConfigurationList']]
        build_conf_ids = build_conf_list['buildConfigurations']
        for build_conf_id in build_conf_ids:
          build_conf = objects[build_conf_id]
          mach_o_type = "staticlib"
          if options.dynamic:
            mach_o_type = "mh_dylib"
          build_conf['buildSettings']['MACH_O_TYPE'] = mach_o_type
          pass
        pass
    with open('project.json', 'w') as framework_project_file_write:
      framework_project_file_write.write(json.dumps(framework_project_obj))
    os.system('plutil -convert xml1 project.json -o '+projectname+'.xcodeproj/project.pbxproj')
    os.chdir('../')

def main():
  parser = OptionParser() 

  parser.add_option(
    "-f", 
    "--file", 
    dest="filepath",
    help="choose config file to create framework"
    )
  parser.add_option(
    "-n",
    "--name",
    dest="projectname",
    help="name of the framework project"
    )
  parser.add_option(
    "-p",
    "--prefix",
    dest="prefix",
    help="bundle id prefix"
    )
  parser.add_option(
    "--organization",
    dest="organizationname",
    help="organization name"
    )
  parser.add_option(
    "-v",
    "--version",
    action="store_true",
    default=False,
    dest="version",
    help="show version and info about the system, and exit"
    )
  parser.add_option(
    "--dynamic",
    action="store_true",
    default=False,
    dest="dynamic",
    help="set Mach-O type to Dynamic Library. Default is Static Library."
    )

  (options, args) = parser.parse_args()

  if options.version:
    print __version__
    sys.exit()

  if options.filepath:
    options_from_file(options.filepath, options)

  if options.projectname == None:
    options.projectname = get_input('project name (AwesomeSDK): ', 'AwesomeSDK')

  if options.prefix == None:
    options.prefix = get_input('bundle id prefix (com.awesome): ', 'com.awesome')

  if options.organizationname == None:
    options.organizationname = get_input('organization name (Awesome Kit): ', 'Awesome Kit')

  if options.dynamic == False:
    options.dynamic = get_input('Is dynamic library (false): ', False)

  options.date = time.strftime('%Y/%m/%d',time.localtime(time.time()))
  options.author = getpass.getuser()

  projectname = options.projectname

  clone_template_project(projectname)

  edit_template_project(options)

  install_pod_dependencies(projectname)

  edit_project_file(options, projectname)

  shutil.rmtree('.git')
  os.system('open '+projectname+'.xcworkspace')
  print 'complete :)'


if __name__ == '__main__':
  main()