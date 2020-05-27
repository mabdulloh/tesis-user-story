import os, sys, getopt

from core.wellformed import *
from core.analyzer import *
from core.globals import *
from core.stories import *
from argparse import ArgumentParser

def main(argv):
  inputfile = ''
  outputfile = ''
  outputformat = 'txt'

  try:
    opts, args = getopt.getopt(argv,"i:o:f:",["ifile=","ofile=","oformat="])
  except getopt.GetoptError:
    print ('  The right way to invoke the program is: \n  python aqusacore.py -i <inputfile>  [-o <outputfile>] [-f <outputformat>] ,\n  with <outputformat> being txt or html')
    sys.exit(2)
  # check cli args
  for opt,arg in opts:
    if opt == 'h':
      sys.exit()
    elif opt == '-i':
      inputfile = arg
    elif opt == '-f':
      outputformat = arg
    elif opt == '-o':
      outputfile = arg
  
  if inputfile == '':
    print('The input file is invalid')
    sys.exit()
  
  if os.path.exists('input/' + inputfile):
    with open('input/' + inputfile) as input:
      raw = input.readlines()
  else:
    print('The file does not exist')
    sys.exit(2)

  allStories = Stories(inputfile)
  init_format(outputformat)

  i = 0
  for line in raw:
    i = i + 1
    if line.strip() == "":
      continue
    story = Story(id = i, title = line.strip())
    story = story.chunk()
    WellFormedAnalyzer.well_formed(story)
    Analyzer.atomic(story)
    Analyzer.clear(story)
    allStories.add_story(story)

    output_text = ""

    if outputformat == 'html':
      with tag('html'):
        with tag('head'):
          with tag('script', src='sorttable.js', type='text/javascript'):
            pass
          with tag('link', rel='stylesheet', href='styles.css'):
            pass
          with tag('body'):
            with tag('table', klass='sortable'):
              with tag('thead'):
                with tag('tr'):
                  with tag('th'):
                    text('ID')
                  with tag('th'):
                    text('User story')
                  with tag('th'):
                    text('Defect type')
                  with tag('th'):
                    text('Note')
              with tag('tbody'):
                for defect in defects:
                  defect.print_html(doc, tag, text)
      output_text = doc.getvalue()
    else:
      for defect in defects:
        output_text = output_text + defect.print_txt()

  if outputfile == '':
    print (output_text)
  else:
    input = open("output/" + outputfile + "." + outputformat, "w")
    input.write(output_text) 
	
if __name__ == "__main__":
   main(sys.argv[1:])