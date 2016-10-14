import json
with open('data/readworksTrainTest/readworks_grade2.dev.0.1.json', 'r') as op:
  lines = op.read()
  jlines = json.loads(lines)



for exjson in jlines['exercises']:
  qjsons = []
  for qjson in exjson['questions']:
    correct_q = True
    for ansjson in qjson['answerChoices']:
      if ansjson['label'] not in 'ABC':
        correct_q = False
    if correct_q:
      qjsons.append(qjson)
  exjson['questions'] = qjsons

with open('data/readworksTrainTest/readworks_grade2.dev.0.1.json', 'w') as fw:
  fw.write(json.dumps(jlines))

