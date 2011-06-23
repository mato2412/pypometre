#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys
import pprint
from dataStructures import *
from pypometre_optparser import opt_parser_pypometre
#from optparse import OptionParser
#import types

import time
import tool_numpy as tn

# recupere le fichier mod_name dans le dossier typ et charge Module_name
def getClassOf(typ, name):
  fileName = "%s.mod_%s"%(typ, name)
  className = "Module_%s"%(name)
  mod = __import__(fileName, None, None, [className], -1)
  class_ = getattr(mod, className)
  return class_

# renvoi la matrice identite _n*_n normalise (matrice de convolution)
def getMatrixId(_n) :
  f = []
  val = 1. / _n
  for i in xrange(_n) :
    line = [val if(i==j) else 0 for j in xrange(_n)]
    f.append(line)
  return f

def getMatrixCenter(_n) :
  f = []
  val = 1. / (_n - 1)
  for i in xrange(_n) :
    line = [val if(i==j) else 0 for j in xrange(_n)]
    f.append(line)
  c = int(_n/2) + 1
  f[c][c] = 0
  return f

def main(args=sys.argv[1:]):
    path_log1 = "./log/documentDistances"
    path_log2 = "./log/documentDistanceFilters"

    parser = opt_parser_pypometre()
    
    (opt_options, opt_args) = parser.parse_args(args)
    opt_fileout = opt_options.fileout

    signature = str(opt_options)

    context = {}
    matrix_id = getMatrixId(5)
#    matrix_id = getMatrixCenter(5)

    context["convolve"] = matrix_id
    context["threshold"] = (0.0,0.7)

    if len(opt_options.segmenter) > 1 :
      context["segmenter_n"] = int(opt_options.segmenter[1])

#choix du documentSegmenter
    documentSegmenter = getClassOf("documentSegmenters", opt_options.segmenter[0])(context)
#choix du segmentDistance
    segmentDistance = getClassOf("segmentDistances", opt_options.segmentDistance)(context)
#choix du documentFilter
    filters =[getClassOf("documentFilters",x)(context) for x in opt_options.documentFilter]
#choix des documentDistancesFilters
    documentDistanceFilters = []
    for x in opt_options.documentDistanceFilter :
      documentDistanceFilters.append(getClassOf("documentDistancesFilters",x)(context))
#choix du documentDistance
    documentDistance = getClassOf("documentDistances", opt_options.documentDistance)(context)

    if(opt_options.verbose) :
      print '[ok] Creating corpus, filtering documents, building segments distances matrices'

    segmented_corpus = []
    for fileName in opt_args :
      try:
        content = Document(fileName)
        for f in filters :
          content = f(content)
        content = documentSegmenter(content)
        segmented_corpus.append(content)
      except Exception, e:
        pass

    len_segmented_corpus = len(segmented_corpus)
    lmatrix_docDist = LinedMatrix(len_segmented_corpus, len_segmented_corpus)

    for i, document1 in enumerate(segmented_corpus):
      segLst1 = document1.getSegmentation()
      name_doc1 = os.path.split(str(document1))[1]
      for j, document2 in enumerate(segmented_corpus):
        if j <= i:
          continue

        if(opt_options.verbose) :
          print "[go] distance(%s,%s)"%(document1, document2)

        segLst2 = document2.getSegmentation()
        name_doc2 = os.path.split(str(document2))[1]

#        matrix = DistMatrix(len(segLst1), len(segLst2))
        matrix = LinedMatrix(len(segLst1), len(segLst2))
        for x, seg1 in enumerate(segLst1):
          for y, seg2 in enumerate(segLst2):
            distance = segmentDistance(seg1, seg2)
            matrix.set(x, y, distance)

#        if(opt_options.verbose) :
#          tn.matrix2image(matrix,"%s/%s_x_%s.png"%(path_log1,name_doc1,name_doc2))

        for f in documentDistanceFilters :
          matrix = f(matrix)
#          if(opt_options.verbose) :
#            tn.matrix2image(matrix,"%s/%s_x_%s%i.png"%(path_log2,name_doc1,name_doc2,nb))

        distance = documentDistance(matrix)
        
        if(opt_options.verbose) :
          print "[ok] distance(%s,%s) = %0.2f "%(document1, document2, distance)
        lmatrix_docDist.set(i,j,distance)
        lmatrix_docDist.set(j,i,distance)

    list_str_document = [str(doc) for doc in segmented_corpus]
    print_json = '''
{"signature" : "%s",\n 
 "filenames" : %s, \n 
 "corpus_scores" : %s \n
}'''%(signature,str(list_str_document),str(lmatrix_docDist))

    if(opt_options.verbose) :
      print "[out] writing :", opt_options.fileout

    file_out = open(opt_options.fileout,'w')
    file_out.write(print_json)
    file_out.close()
    return print_json

if __name__ == "__main__":
    start = time.clock()
    main()
    end = time.clock()
    print "[time] %f"%(end-start)
