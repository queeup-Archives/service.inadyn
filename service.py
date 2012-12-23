# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import sys
import os
import re
import signal
import xbmc
import xbmcaddon

# DEBUG
DEBUG = True

__addon__ = xbmcaddon.Addon()
__plugin__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon')
__path__ = __addon__.getAddonInfo('path')
__cachedir__ = __addon__.getAddonInfo('profile')
__settings__ = __addon__.getSetting


def check(process):
  p1 = Popen(['ps', 'ax', '-o', 'pid,args'], shell=False, stdout=PIPE, stderr=PIPE, close_fds=True)
  p2 = Popen(['grep', process], shell=False, stdin=p1.stdout, stdout=PIPE, stderr=PIPE, close_fds=True)
  p3 = Popen(['grep', '-v', 'grep'], shell=False, stdin=p2.stdout, stdout=PIPE, stderr=PIPE, close_fds=True)
  stdout, stderr = p3.communicate()
  if stdout:
    pid = re.findall('(\d+)', stdout)[0]
    return True, pid
  return False, None


def execute(arg):
  p = Popen(arg, shell=False, stdout=PIPE, close_fds=True)
  pid = p.pid
  if pid:
    return True, pid + 1


def kill(pid):
  os.kill(int(pid), signal.SIGUSR1)


def log(description):
  xbmc.log("[SERVICE] '%s v%s': DEBUG: %s" % (__plugin__, __version__, description.encode('ascii', 'ignore')), xbmc.LOGNOTICE)


def notification(title, message, image=__icon__, displaytime=6000):
  xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "GUI.ShowNotification", "params": {"title": "%s", "message": "%s", "image": "%s", "displaytime": %i}, "id": "%s"}' % \
                      (title, message, image, displaytime, __addon__.getAddonInfo('id')))

# Get settings
INADYN_START = __settings__('INADYN_START')
INADYN_SYSTEM = __settings__('INADYN_SYSTEM')
INADYN_UPDATE = int(__settings__('INADYN_UPDATE')) * 60000
INADYN_HOST = __settings__('INADYN_HOST')
INADYN_USER = __settings__('INADYN_USER')
INADYN_PWD = __settings__('INADYN_PWD')
INADYN_DBG = __settings__('INADYN_DBG')

INADYN_EXEC = '%s/bin/inadyn' % __path__
INADYN_LOG = '%sinadyn.log ' % xbmc.translatePath(__cachedir__)

inadyn = [INADYN_EXEC, \
          '--update_period', str(INADYN_UPDATE), \
          '--alias', INADYN_HOST, \
          '--username', INADYN_USER, \
          '--password', INADYN_PWD, \
          '--log_file', INADYN_LOG, \
          '--verbose', INADYN_DBG, \
          '--background', ]

# dnsomatic support
if INADYN_SYSTEM == 'dnsomatic@dyndns.org':
  inadyn += ['--dyndns_server_name', 'updates.dnsomatic.com', \
             '--dyndns_server_url', '/nic/update?']
else:
  inadyn += ['--dyndns_system', INADYN_SYSTEM]

# if not executable change permission
if not os.access('%s/bin/inadyn' % __path__, os.X_OK):
  os.chmod('%s/bin/inadyn' % __path__, 0755)

# check if inadyn already running. If running find pid number
_status, _pid = check('inadyn')
if not _status:
  # check settings is allowing for service start with xbmc
  if INADYN_START == 'true':
    # Start service
    status, _pid = execute(inadyn)
    if status:
      if DEBUG:
        log('inadyn starting!')
  else:
    if DEBUG:
      log('inadyn service disabled from settings!!!')
    sys.exit()
else:
  if DEBUG:
    log('inadyn already running!')

while (not xbmc.abortRequested):
  xbmc.sleep(bool(0.250))

# kill inadyn before xbmc
kill(_pid)
if DEBUG:
  log('inadyn stoping!')
xbmc.sleep(1)
sys.exit()