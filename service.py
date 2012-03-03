# -*- coding: utf-8 -*-

# Debug
Debug = True

import xbmc, xbmcaddon, os, datetime, time, re, signal
from subprocess import Popen, PIPE

__addon__ = xbmcaddon.Addon(id='service.inadyn')
__info__ = __addon__.getAddonInfo
__plugin__ = __info__('name')
__version__ = __info__('version')
__icon__ = __info__('icon')
__path__ = __info__('path')
__cachedir__ = __info__('profile')
__language__ = __addon__.getLocalizedString
__settings__ = __addon__.getSetting
__set_settings__ = __addon__.setSetting

STARTUP = True
now = datetime.datetime.now()

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
  time.sleep(1)
  os.kill(int(pid), signal.SIGUSR1)

def LOG(description):
    xbmc.log("[SERVICE] '%s v%s': DEBUG: %s" % (__plugin__, __version__, description.encode('ascii', 'ignore')), xbmc.LOGNOTICE)

def notification(title, message):
    xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % \
                                     (title.encode('utf-8', 'ignore'), message.encode('utf-8', 'ignore'), 6000, __icon__))
# thanks to @amet
def waiter(seconds, pid):
  LOG("Delaying %s secs" % seconds)
  for i in range(1, seconds):
    time.sleep(1)
    # kill inadyn before xbmc
    if xbmc.abortRequested == True:
      #os.system('killall inadyn')
      kill(pid)
      if Debug: LOG('inadyn stoping!')
      time.sleep(1)
      sys.exit()

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

inadyn = [INADYN_EXEC , \
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

# check settings is allowing for service start with xbmc
if INADYN_START == 'true':
  while (not xbmc.abortRequested):
    if STARTUP:
      # make False for run service 1 time
      STARTUP = False
      _status, _pid = check('inadyn')
      if not _status:
        # if not executable change permission
        if not os.access('%s/bin/inadyn' % __path__, os.X_OK):
          os.chmod('%s/bin/inadyn' % __path__, 0755)
        # Start service
        status, pid = execute(inadyn)
        if status:
          if Debug: LOG('inadyn starting!')
          #notification('inadyn service', 'Successfully started!')
      else:
        if Debug: LOG('inadyn already running!')
        pid = _pid
    if datetime.datetime.now().minute >= ((now.minute / 5) * 5) + 5 or (datetime.datetime.now().hour > now.hour) or (datetime.datetime.now().hour == 1 and now.hour == 12) or (datetime.datetime.now().hour == 0 and now.hour == 23) :
      wait = 240
    else:
      wait = 3
    waiter(wait, int(pid))
else:
  if Debug: LOG('inadyn service disabled from settings!!!')
  sys.exit()