import json
import random
import re

with open('readworks_gradek.0.1.json', 'r') as op:
    lines = op.read()

jlines = json.loads(lines)

def alwaysA(stjson, qjson):
  return "A"

def alwaysB(stjson, qjson):
  return "B"

def randomAB(stjson, qjson):
  tmp = random.random()
  if tmp > 0.5:
    return "A"
  else:
    return "B"

def mostFreq(stjson, qjson):
  tklist = re.compile(r"\w+").findall(stjson['text'].lower())
  freqdict = {}
  for ansjson in qjson['answerChoices']:
    freqdict[ansjson['label']] = tklist.count(ansjson['text'])
  if freqdict['A'] > freqdict['B']:
    return "A"
  if freqdict['A'] < freqdict['B']:
    return "B"
  return randomAB(stjson, qjson)

def testAll(answer_func, rawjson, print_false = False):
  correct = 0
  total = 0
  for exjson in rawjson['exercises']:
    for qjson in exjson['questions']:
      total += 1
      compans = answer_func(exjson['story'], qjson)
      if compans == qjson['correctAnswer']:
        correct += 1
      else:
        if print_false:
          print exjson['story']['text']
          print qjson['text']
          print [tt['text'] for tt in qjson['answerChoices']]
  return correct / float(total)


if __name__ == "__main__":
  print "always A"
  print testAll(alwaysA, jlines)
  print "always B"
  print testAll(alwaysB, jlines)
  print "randomAB"
  print testAll(randomAB, jlines)
  print "mostFreq"
  print testAll(mostFreq, jlines, True)


