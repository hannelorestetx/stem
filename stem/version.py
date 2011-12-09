"""
Tor versioning information and requirements for its features. These can be
easily parsed and compared, for instance...

>>> my_version = stem.version.get_system_tor_version()
>>> print my_version
0.2.1.30
>>> my_version > stem.version.Requirement.CONTROL_SOCKET
True

get_system_tor_version - gets the version of our system's tor installation
Version - Tor versioning information.
  |- __str__ - string representation
  +- __cmp__ - compares with another Version

Requirement - Enumerations for the version requirements of features.
  |- GETINFO_CONFIG_TEXT - 'GETINFO config-text' query
  +- CONTROL_SOCKET      - 'ControlSocket <path>' config option
"""

import re
import logging

import stem.util.enum
import stem.util.system

LOGGER = logging.getLogger("stem")

# cache for the get_tor_version function
VERSION_CACHE = {}

def get_system_tor_version(tor_cmd = "tor"):
  """
  Queries tor for its version. This is os dependent, only working on linux,
  osx, and bsd.
  
  Arguments:
    tor_cmd (str) - command used to run tor
  
  Returns:
    stem.version.Version provided by the tor command
  
  Raises:
    IOError if unable to query or parse the version
  """
  
  if not tor_cmd in VERSION_CACHE:
    try:
      version_cmd = "%s --version" % tor_cmd
      version_output = stem.util.system.call(version_cmd)
    except OSError, exc:
      raise IOError(exc)
    
    if version_output:
      # output example:
      # Oct 21 07:19:27.438 [notice] Tor v0.2.1.30. This is experimental software. Do not rely on it for strong anonymity. (Running on Linux i686)
      # Tor version 0.2.1.30.
      
      last_line = version_output[-1]
      
      if last_line.startswith("Tor version ") and last_line.endswith("."):
        try:
          version_str = last_line[12:-1]
          VERSION_CACHE[tor_cmd] = Version(version_str)
        except ValueError, exc:
          raise IOError(exc)
      else:
        raise IOError("Unexpected response from '%s': %s" % (version_cmd, last_line))
    else:
      raise IOError("'%s' didn't have any output" % version_cmd)
  
  return VERSION_CACHE[tor_cmd]

class Version:
  """
  Comparable tor version, as per the 'new version' of the version-spec...
  https://gitweb.torproject.org/torspec.git/blob/HEAD:/version-spec.txt
  
  Attributes:
    major (int)  - major version
    minor (int)  - minor version
    micro (int)  - micro version
    patch (int)  - optional patch level (None if undefined)
    status (str) - optional status tag without the preceding dash such as
                   'alpha', 'beta-dev', etc (None if undefined)
  """
  
  def __init__(self, version_str):
    """
    Parses a valid tor version string, for instance "0.1.4" or
    "0.2.2.23-alpha".
    
    Raises:
      ValueError if input isn't a valid tor version
    """
    
    m = re.match(r'^([0-9]+).([0-9]+).([0-9]+)(.[0-9]+)?(-\S*)?$', version_str)
    
    if m:
      major, minor, micro, patch, status = m.groups()
      
      # The patch and status matches are optional (may be None) and have an extra
      # proceeding period or dash if they exist. Stripping those off.
      
      if patch: patch = int(patch[1:])
      if status: status = status[1:]
      
      self.major = int(major)
      self.minor = int(minor)
      self.micro = int(micro)
      self.patch = patch
      self.status = status
    else: raise ValueError("'%s' isn't a properly formatted tor version" % version_str)
  
  def __str__(self):
    """
    Provides the normal representation for the version, for instance:
    "0.2.2.23-alpha"
    """
    
    suffix = ""
    
    if self.patch:
      suffix += ".%i" % self.patch
    
    if self.status:
      suffix += "-%s" % self.status
    
    return "%i.%i.%i%s" % (self.major, self.minor, self.micro, suffix)
  
  def __cmp__(self, other):
    """
    Simple comparison of versions. An undefined patch level is treated as zero
    and status tags are not included in comparisions (as per the version spec).
    """
    
    if not isinstance(other, Version):
      return 1 # this is also used for equality checks
    
    for attr in ("major", "minor", "micro", "patch"):
      my_version = max(0, self.__dict__[attr])
      other_version = max(0, other.__dict__[attr])
      
      if my_version > other_version: return 1
      elif my_version < other_version: return -1
    
    my_status = self.status if self.status else ""
    other_status = other.status if other.status else ""
    
    # not including tags in comparisons because the spec declares them to be
    # 'purely informational'
    return 0

Requirement = stem.util.enum.Enum(
  ("GETINFO_CONFIG_TEXT", Version("0.2.2.7-alpha")),
  ("CONTROL_SOCKET", Version("0.2.0.30")),
)

