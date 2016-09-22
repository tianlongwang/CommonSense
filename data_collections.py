import json
import random
import re


def tokenize(line):
  return re.compile(r'\w+').findall(line.lower())


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
  #TODO ignoring duplicated tokens, could improve with vector bow
    s1 = set(tokenlist1)
    s2 = set(tokenlist2)
    return float(len(s1.intersection(s2))) / len(s1.union(s2))
  lineA = qjson['text'] + ' ' + qjson['answerChoices'][0]['text']
  lineB = qjson['text'] + ' ' + qjson['answerChoices'][1]['text']
  tlA = tokenize(lineA)
  tlB = tokenize(lineB)
  Amatch = []
  Bmatch = []
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

def testAll(answer_func, rawjson, print_false = False):
  correct = 0
  total = 0
  for exjson in rawjson['exercises']:
    for qjson in exjson['questions']:
      total += 1
      if callable(answer_func):
        compans = answer_func(exjson['story'], qjson)
      else:
        compans = answer_func
      if compans == qjson['correctAnswer']:
        correct += 1
      else:
        if print_false:
          print exjson['story']['text']
          print qjson['text']
          print [tt['text'] for tt in qjson['answerChoices']]
  return correct / float(total)

def labelSet(rawjson):
  options = set()
  for exjson in rawjson['exercises']:
    for qjson in exjson['questions']:
      for ansjson in qjson['answerChoices']:
        options.add(ansjson['label'])
  return list(options)

if __name__ == "__main__":
  for gg in ['k','1','2','3', '4']:
    print "\n ------- grade " + gg + " -------\n"
    with open('readworks_grade' + gg + '.0.1.json', 'r') as op:
      lines = op.read()
    jlines = json.loads(lines)
    for lb in labelSet(jlines):
      print "always " + lb
      print testAll(always(lb), jlines)
    print "randomChoice"
    print testAll(randomChoice, jlines)
    print "mostFreq"
    print testAll(mostFreq, jlines)
    print "BOW"
    print testAll(bowMatch, jlines)

