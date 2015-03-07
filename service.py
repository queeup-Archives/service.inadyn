# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import os
import signal
import xbmc
import xbmcaddon

# DEBUG
DEBUG = True

addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo('name')
addon_version = addon.getAddonInfo('version')
addon_icon = addon.getAddonInfo('icon')
addon_path = addon.getAddonInfo('path')
addon_cachedir = addon.getAddonInfo('profile')
addon_settings = addon.getSetting


def log(description):
  xbmc.log("[DEBUG] '%s v%s': %s" % (addon_name, addon_version, description.encode('ascii', 'ignore')), xbmc.LOGNOTICE)


def notification(title, message, image=addon_icon, displaytime=6000):
    xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "GUI.ShowNotification", "params": {"title": "%s", "message": "%s", "image": "%s", "displaytime": %i}, "id": "%s"}' % \
                        (title, message, image, displaytime, addon.getAddonInfo('id')))


class Monitor(xbmc.Monitor):
  def __init__(self, *args, **kwargs):
    xbmc.Monitor.__init__(self)
    self.restart = kwargs['restart']

  def onSettingsChanged(self):
    log('Settings Changed!')
    self.restart()


class Main:
  def __init__(self):
    self._init_vars()
    # if not executable change permission
    if not os.access(self.INADYN_EXEC, os.X_OK):
      os.chmod(self.INADYN_EXEC, 0755)
    self._daemon()

  def _init_vars(self):
    self.pid = None
    self._get_settings()
    self._monitor = Monitor(restart=self.restart_service)
     
  def _get_settings(self):
    # Get settings
    self.INADYN_START = addon_settings('INADYN_START')
    self.INADYN_SYSTEM = addon_settings('INADYN_SYSTEM')
    self.INADYN_UPDATE = int(addon_settings('INADYN_UPDATE')) * 60
    self.INADYN_HOST = addon_settings('INADYN_HOST')
    self.INADYN_USER = addon_settings('INADYN_USER')
    self.INADYN_PWD = addon_settings('INADYN_PWD')
    self.INADYN_DBG = addon_settings('INADYN_DBG')
    
    # arm support
    if 'arm' in os.uname()[4]:
      self.INADYN_EXEC = '%s/bin/inadyn.arm' % addon_path
    else:
      # i386/i686/x86_64 binary support
      self.INADYN_EXEC = '%s/bin/inadyn.%s' % (addon_path, os.uname()[4])
    self.INADYN_LOG = '%sinadyn.log' % xbmc.translatePath(addon_cachedir)
    self.INADYN_PID = '%sinadyn.pid' % xbmc.translatePath(addon_cachedir)

    if int(addon_settings('INADYN_SYSTEM_CONFIG')) == 1:
      self.inadyn = [self.INADYN_EXEC,
                     '--period', str(self.INADYN_UPDATE),
                     '--system', 'custom@http_srv_basic_auth',
                     '--server-name', addon_settings('MANUAL_INADYN_SERVER_NAME'),
                     '--server-url', addon_settings('MANUAL_INADYN_SERVER_URL'),
                     '--alias', self.INADYN_HOST,
                     '--username', self.INADYN_USER,
                     '--password', self.INADYN_PWD,
                     '--logfile', self.INADYN_LOG,
                     '--pidfile', self.INADYN_PID,
                     '--cache-dir', xbmc.translatePath(addon_cachedir),
                     '--verbose', self.INADYN_DBG,
                     '--background', ]
    else:
      self.inadyn = [self.INADYN_EXEC,
                     '--period', str(self.INADYN_UPDATE),
                     '--system', self.INADYN_SYSTEM,
                     '--alias', self.INADYN_HOST,
                     '--username', self.INADYN_USER,
                     '--password', self.INADYN_PWD,
                     '--logfile', self.INADYN_LOG,
                     '--pidfile', self.INADYN_PID,
                     '--cache-dir', xbmc.translatePath(addon_cachedir),
                     '--verbose', self.INADYN_DBG,
                     '--background', ]

  def check(self):
    # check if pid file exist
    if os.path.isfile(self.INADYN_PID):
      # read pid from pid file
      with open(self.INADYN_PID, 'r') as pid:
        # check if process exist
        if os.path.exists("/proc/%s" % pid.read()):
          # process and pid file exist
          return True, int(pid.read())
        # if pid file exist but process not exist
        else:
          # remoce pid file.
          os.unlink(self.INADYN_PID)
          return False, None
    else:
      return False, None

  def execute(self, arg):
    p = Popen(arg, shell=False, stdout=PIPE, close_fds=True)
    self.pid = p.pid + 1
    p.communicate()
    if self.pid:
      return True, self.pid

  def kill(self, pid):
    try:
      os.kill(int(pid), signal.SIGTERM)
    except OSError:
      os.kill(int(pid) + 1, signal.SIGTERM)

  def start_service(self):
    # check settings is allowing for service start with xbmc
    if self.INADYN_START == 'true':
      # check if inadyn already running. If running find pid number
      _status, self.pid = self.check()
      if not _status:
        # Start service
        status, self.pid = self.execute(self.inadyn)
        if status:
          if DEBUG:
            log('Service starting!')
      else:
        if DEBUG:
          log('Service already running!')
    else:
      if DEBUG:
        log('Service disabled from settings!')
      # notification(addon_name, 'inadyn service disabled from settings!!!')

  def stop_service(self):
    self.kill(self.pid)

  def restart_service(self):
    self.stop_service()
    # del self.pid because when restart, self.pid keeps old and wrong variable.
    del self.pid
    if DEBUG:
      log('Service restarting!')
    # get new settings for inadyn execute
    self._get_settings()
    # start inadyn with new settings
    self.start_service()
  
  def _daemon(self):
    self.start_service()
    while True:
      if self._monitor.waitForAbort(1):
        log('Abort requested!')
        break
      xbmc.sleep(500)
    log('Service stoping!')
    self.stop_service()
    del self._monitor

if __name__ == "__main__":
  Main()