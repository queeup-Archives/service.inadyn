# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import os
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


def log(description):
    xbmc.log("[SERVICE] '%s v%s': DEBUG: %s" % (__plugin__, __version__, description.encode('ascii', 'ignore')), xbmc.LOGNOTICE)


class Monitor(xbmc.Monitor):
  def __init__(self, *args, **kwargs):
    xbmc.Monitor.__init__(self)
    self.restart = kwargs['restart']
    self.stop = kwargs['stop']

  def onSettingsChanged(self):
    log('Settings Changed!')
    self.restart()

  def onAbortRequested(self):
    log('Stoping Inadyn Service!')
    self.stop()


class Main:
  def __init__(self):
    self.pid = None
    self._get_settings()
    # self._monitor = Monitor(action=self.restart_service)
    self._monitor = Monitor(restart=self.restart_service, stop=self.stop_service)
    # if not executable change permission
    if not os.access(self.INADYN_EXEC, os.X_OK):
      os.chmod(self.INADYN_EXEC, 0755)
    self.start_service()

  def _get_settings(self):
    # Get settings
    self.INADYN_START = __settings__('INADYN_START')
    self.INADYN_SYSTEM = __settings__('INADYN_SYSTEM')
    self.INADYN_UPDATE = int(__settings__('INADYN_UPDATE')) * 60
    self.INADYN_HOST = __settings__('INADYN_HOST')
    self.INADYN_USER = __settings__('INADYN_USER')
    self.INADYN_PWD = __settings__('INADYN_PWD')
    self.INADYN_DBG = __settings__('INADYN_DBG')

    # i386/i686/x86_64/arm binary support
    self.INADYN_EXEC = '%s/bin/inadyn.%s' % (__path__, os.uname()[4])
    self.INADYN_LOG = '%sinadyn.log' % xbmc.translatePath(__cachedir__)
    self.INADYN_PID = '%sinadyn.pid' % xbmc.translatePath(__cachedir__)

    if int(__settings__('INADYN_SYSTEM_CONFIG')) == 1:
      self.inadyn = [self.INADYN_EXEC,
                     '--period', str(self.INADYN_UPDATE),
                     '--system', 'custom@http_srv_basic_auth',
                     '--server-name', __settings__('MANUAL_INADYN_SERVER_NAME'),
                     '--server-url', __settings__('MANUAL_INADYN_SERVER_URL'),
                     '--alias', self.INADYN_HOST,
                     '--username', self.INADYN_USER,
                     '--password', self.INADYN_PWD,
                     '--logfile', self.INADYN_LOG,
                     '--pidfile', self.INADYN_PID,
                     '--cache-dir', xbmc.translatePath(__cachedir__),
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
                     '--cache-dir', xbmc.translatePath(__cachedir__),
                     '--verbose', self.INADYN_DBG,
                     '--background', ]

    if (__settings__('INADYN_SSL').lower() == 'true'):
      self.inadyn.append('--ssl')

  def check(self):
    # check if pid file exist
    if os.path.isfile(self.INADYN_PID):
      # read pid from pid file
      with open(self.INADYN_PID, 'r') as pid:
        return True, int(pid.read())
    else:
      return False, None

  def execute(self, arg):
    p = Popen(arg, shell=False, stdout=PIPE, close_fds=True)
    pid = p.pid + 1
    p.communicate()
    if pid:
      self.pid = pid
      return True, pid

  def kill(self, pid):
    os.kill(int(pid), signal.SIGTERM)

  def notification(self, title, message, image=__icon__, displaytime=6000):
    xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "GUI.ShowNotification", "params": {"title": "%s", "message": "%s", "image": "%s", "displaytime": %i}, "id": "%s"}' % \
                        (title, message, image, displaytime, __addon__.getAddonInfo('id')))

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
              log('inadyn starting!')
      else:
        if DEBUG:
          log('inadyn already running!')

      while not xbmc.abortRequested:
        xbmc.sleep(bool(0.250))

    else:
      if DEBUG:
        log('inadyn service disabled from settings!!!')
      # notification(__plugin__, 'inadyn service disabled from settings!!!')

  def stop_service(self):
    self.kill(self.pid)
    del self._monitor

  def restart_service(self):
    self.kill(self.pid)
    # del self.pid because when restart, self.pid keeps old and wrong variable.
    del self.pid
    if DEBUG:
      log('inadyn restarting!')
    # get new settings for inadyn execute
    self._get_settings()
    # start inadyn with new settings
    self.start_service()

if __name__ == "__main__":
  Main()
