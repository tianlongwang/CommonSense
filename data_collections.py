import json
import os
import random
import re
from sys import argv
from nltk.stem import WordNetLemmatizer
from nltk import word_tokenize
from nltk import sent_tokenize
import numpy as np
from ipdb import set_trace
lemmatizer = WordNetLemmatizer()
import difflib


from nltk import pos_tag

def tokenize(line):
  return [lemmatizer.lemmatize(tmp) for tmp in word_tokenize(line.lower())]

def always(label, *args):
  return label

def randomChoice(stjson, qjson):
  options = set()
  for ansjson in qjson['answerChoices']:
    options.add(ansjson['label'])
  return random.sample(options,1)[0]

def mostFreq(stjson, qjson):
  tklist = tokenize(stjson['text'])
  freqdict = {}
  for ansjson in qjson['answerChoices']:
    freqdict[ansjson['label']] = tklist.count(ansjson['text'])
  #print "\n", qjson
  maxK = ''
  maxV = 0.
  for key in freqdict:
    if freqdict[key] > maxV:
      maxV = freqdict[key]
      maxK = key
  if maxK == '':
    return randomChoice(stjson, qjson)
  else:
    return maxK


def bowMatch(stjson, qjson):
  def tokensMatch(tokenlist1, tokenlist2):
    #return difflib.SequenceMatcher(None, tokenlist1, tokenlist2).ratio() # list similarity, not as good as set similarity
    s1 = set(tokenlist1)
    s2 = set(tokenlist2)
    return float(len(s1.intersection(s2))) / len(s1.union(s2)) # set similarity
  labels = list('ABCDE')
  #set_trace()
  ansDict = dict([(ansjson['label'], ansjson['text']) for ansjson in qjson['answerChoices']])
  qaLine = []
  for lb in labels:
    if lb in ansDict:
        qaLine.append(qjson['text'] + ' ' + ansDict[lb])
    else:
        break
  #print len(qaLine)
  tLine = [tokenize(tmp) for tmp in qaLine]
  mcMatch = []
  for tl in tLine:
    tm = []
    for sline in sent_tokenize(stjson['text']):
        tm.append(tokensMatch(tl, tokenize(sline)))
    mcMatch.append(max(tm))
  ret = labels[np.argmax(mcMatch)]
  return ret
'''


  lineA = qjson['text'] + ' ' + qjson['answerChoices'][0]['text']
  lineB = qjson['text'] + ' ' + qjson['answerChoices'][1]['text']
  tlA = tokenize(lineA)
  #print tlA
  #print [lemmatizer.lemmatize(tmp) for tmp in tlA]
  #exit(1)
  tlB = tokenize(lineB)
  Amatch = []
  Bmatch = []
  #TODO: sum 3 decrease dramatically.
  for sline in stjson['text'].split('.!?'):
    Amatch.append(tokensMatch(tlA, tokenize(sline)))
    Bmatch.append(tokensMatch(tlB, tokenize(sline)))
  Amax = max(Amatch)
  Bmax = max(Bmatch)
  if Amax > Bmax:
    return "A"
  if Bmax > Amax:
    return "B"
  return randomChoice(stjson, qjson)
'''
def testAll(answer_func, rawjson, print_false = False):
  correct = 0
  total = 0
  nic_count = 0
  for exjson in rawjson['exercises']:
    for qjson in exjson['questions']:
      labels = [ansjson['label']  for ansjson in qjson['answerChoices']]
      labelsABCD = [tp in u'ABCD' for tp in labels]
      if not all(labelsABCD):
        #choices is part of A B C D
        continue
      if qjson['correctAnswer'] not in labels:
        #correct answer in labels
        continue
      ansTexts = [ansjson['text']  for ansjson in qjson['answerChoices']]
      if len(set(ansTexts)) != len(ansTexts):
        #no duplicated answer
        continue
      total += 1
      if callable(answer_func):
        compans = answer_func(exjson['story'], qjson)
      else:
        compans = answer_func
      if compans == qjson['correctAnswer']:
        correct += 1
      else:
        nic, aw = not_in_context(exjson, qjson)
        if print_false and nic:
          nic_count += 1
          print '-------------------------------'
          #print 'in_context', in_context
          print 'STORY ID: ', exjson['story']['id']
          print 'STORY: ', exjson['story']['text']
          print 'QUESTION: ', qjson['text']
          print 'ANSWER: ',  [[tt['label'], tt['text']] for tt in qjson['answerChoices']]
          print 'Computed answer: ', compans
          print 'Correct answer: ', qjson['correctAnswer']
          print 'Alian words: ', aw
  return correct, total, correct / float(total), nic_count



def not_in_context(exjson, qjson):
  not_in = False
  ret = []
  wrong_answers = []
  for ansjson in qjson['answerChoices']:
    if ansjson['label'] != qjson['correctAnswer']:
      wrong_answers.append(ansjson['text'])
  for ansjson in qjson['answerChoices']:
    if ansjson['label'] != qjson['correctAnswer']:
      continue
    for word in tokenize(ansjson['text']):
        #pt = pos_tag([word])
        #if pt[0][1][0] not in ['N','V','J']:
        #    continue
        #print 'word', word
        #print 'wrong_answers', wrong_answers
        in_all_wrong = True
        for wa in wrong_answers:
            if word not in tokenize(wa):
                in_all_wrong = False
        story_token_in_ans = False
        for story_token in tokenize(exjson['story']['text']):
            if story_token in word:
                story_token_in_ans = True
        if word not in exjson['story']['text'].lower() and word not in tokenize(exjson['story']['text']) and not in_all_wrong and not story_token_in_ans:
            not_in = True
            ret.append(word)
  return not_in, ret

def labelSet(rawjson):
  options = set()
  for exjson in rawjson['exercises']:
    for qjson in exjson['questions']:
      for ansjson in qjson['answerChoices']:
        options.add(ansjson['label'])
  return list(options)

if __name__ == "__main__":
  #for gg in ['k','1','2','3', '4']:
  #for gg in ['1.test','1.dev','2.test','2.dev']:
    #if len(argv) > 1:
    #  if gg not in argv:
    #    continue
    #print "\n------- grade " + gg + " -------\n"
  if len(argv) < 2:
    #data_dir = './data/readworksTrainTest2'
    data_dir = './data/readworks'
  else:
    data_dir = argv[1]
  for fn in os.listdir(data_dir):
    fns = fn.split('.')
    if fns[-1] != 'json':
      continue
    #if 'gradek' not in fn:
    #  continue
    path_fn = os.path.join(data_dir, fn)
    with open(path_fn, 'r') as op:
      lines = op.read()
    jlines = json.loads(lines)
    print('\n-------'+fn+'-------')
   # for lb in labelSet(jlines):
   #   print "always choose: " + lb
   #   print testAll(always(lb), jlines)
   # print "randomChoice"
   # print testAll(randomChoice, jlines)
   # print "mostFreq"
   # print testAll(mostFreq, jlines)
    print "BOW"
    print testAll(bowMatch, jlines)#, True)

