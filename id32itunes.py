import sys
import os
import shutil
import urllib
import elementtree.ElementTree as et
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
    SubElement(e, "key").text     = key
    SubElement(e,  valtype).text  = val
    
    
    
    


class Syncer(object):
  r2itunes = {1:20, 2:40, 3:60, 4:80, 5:100}
  
  def __init__(self):
    self.rootfolder = ('file://localhost/Users/Tom/Music/', 'Z:/Tom/Media/Music/')    
  
  def processtrack(self, e):
    d = parsedict(e)
    filepath = urllib.unquote(d['Location'].text)
    
    #print ('\b'*80),
    print ('Processing %s' % filepath),
    
    try:
      id3 = ID3(filepath.replace(*self.rootfolder))
    except:
      print 'Failed to open ID3 tags'
      return

    try:
      rating = self.r2itunes[int(id3['TXXX:rating'].text)]
      setdict(e, d, 'Rating', 'integer', str(rating))
      print 'Rating = %s' % rating
    except:
      # no rating set
      pass
    
    #      <key>Play Count</key><integer>1</integer>
    #      <key>Play Date</key><integer>3341475263</integer>
    #      <key>Play Date UTC</key><date>2009-11-19T18:34:23Z</date>
    try:
      playcount = self.r2itunes[int(id3['TXXX:play_count'].text)]
      setdict(e, d, 'Play Count', 'integer', str(playcount))
      print 'Play Count = %s' % playcount
    except:
      # no play count set
      pass
    
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
    self.library = et.parse(self.library_name)
    print 'Processing..'
    self.walklibrary(self.library.getroot())
    print 'Writing library..' 
    self.library.write(self.library_name)
    print 'Done!'
    
  
  


if __name__ == '__main__':
  Syncer().main()