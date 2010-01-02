# Script to import MP3 metadata from ID3 tags into an iTunes database,
# because iTunes is too retarded to read/write to standard formats
# and uses its own proprietarty format.
#
#
# Directions
# ==========
#
# 0. Have file statistics (ratings, playcounts) in ID3 tags that you want in iTunes (This may take 4 hours)
# 1. Import all your music into iTunes normally. iTunes will ignore the data you want.
# 2. Close iTunes. Do not open it again until step 6.
# 3. Copy `/USERNAME/Music/iTunes/iTunes Music Library.xml` and `/USERNAME/Music/iTunes/iTunes Library` to a safe place
# 4. DELETE `/USERNAME/Music/iTunes/iTunes Music Library.xml` and `/USERNAME/Music/iTunes/iTunes Library`
#    This might fuck up other things that iTunes knows.
# 5. run id32itunes.py `/safeplace/iTunes Music Library.xml` (This may take 4 hours)
# 6. open iTunes. AAAHH, all your data is gone!
# 7. in iTunes, go File->Library->Import Playlist, select `/safeplace/iTunes Music Library.xml` (This may take 4 hours)
# 8. Done!
# 9. if it fucks up, restore `/USERNAME/Music/iTunes/iTunes Music Library.xml` and `/USERNAME/Music/iTunes/iTunes Library` from backup
#

import sys
import os
import re
import shutil
import urllib
import elementtree.ElementTree as ET
sys.path.append('./mutagen')
from mutagen.id3 import ID3


def parsedict(e):
  assert e.tag == 'dict'
  d = {}
  key = None
  for i in e:
    if i.tag == 'key':
      key = i.text
    else:
      assert not key in d, (key, d[key].text, i.text)
      d[key] = i
  return d
  
def setdict(e, d, key, valtype, val):
  if not d: d = parsedict(e)
  if key in d:
    d[key].text = val
  else:
    ET.SubElement(e, "key").text     = key
    ET.SubElement(e,  valtype).text  = val
    
    
def decode(s):
  def f(m):
    i = m.group(1)
    try:    return unichr(int(i))
    except: return i
  return re.sub("&#(\d+)(;|(?=\s))", f, s)

    


class Syncer(object):
  r2itunes = {1:20, 2:40, 3:60, 4:80, 5:100}
  
  def __init__(self):
    self.rootfolder = ('file://localhost/Users/Tom/Music/', 'Z:/Tom/Media/Music/')    
    self.n_rating    = 0
    self.n_playcount = 0
    self.n_failed    = 0
    
  
  def processtrack(self, e):
    d = parsedict(e)
    
    try:
      filepath = decode(urllib.unquote(d['Location'].text))
      print ('P: %s' % os.path.basename(filepath))    
      id3 = ID3(filepath.replace(*self.rootfolder))
    except:
      print 'E: Failed to open file'
      self.n_failed += 1
      return
    
    def gettag(tags):
      v = None
      for t in tags:
        v = v or id3.get(t)
      if v: v = v.text[0]
      return v      
    
    #      <key>Rating</key><integer>20</integer></dict>
    #      <key>Play Count</key><integer>1</integer>
    #      <key>Play Date</key><integer>3341475263</integer>
    #      <key>Play Date UTC</key><date>2009-11-19T18:34:23Z</date>      
    v = gettag(['TXXX:rating', 'TXXX:RATING'])
    if v and int(v):
      v = self.r2itunes[int(v)]
      setdict(e, d, 'Rating', 'integer', str(v))
      self.n_rating += 1
      print '      Rating = %r' % v
    
    v = gettag(['TXXX:play_count'])
    if v:
      setdict(e, d, 'Play Count', 'integer', str(int(v)))
      self.n_playcount += 1
      print '      Play Count = %r' % v
      
    
  def walklibrary(self, root):
    d = parsedict(root[0])
    tracks = parsedict(d['Tracks'])
    
    for i in tracks.itervalues():
      self.processtrack(i)

  def main(self):
    try:
      self.library_name = sys.argv[1]
      if not os.path.isfile(self.library_name):
        print "'%s' not found" % self.library_name
        raise Exception
    except Exception, e:
      print e
      print 'Usage: id32itunes itunes_library.xml'
      sys.exit(1)
    
    print 'Backing up library..'
    shutil.copy(self.library_name, self.library_name + '.bak')
    print 'Reading library..'
    self.library = ET.parse(self.library_name)
    print 'Processing..'
    self.walklibrary(self.library.getroot())
    print 'Writing library..' 
    self.library.write(self.library_name)
    print 'Done!'
    print 'Wrote %5d ratings'     % self.n_rating
    print 'Wrote %5d play counts' % self.n_playcount
    print 'Failed to read %d files' % self.n_failed


if __name__ == '__main__':
  Syncer().main()