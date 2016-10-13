"""Semantic Tensor QA, use Glove as initialization for word embedding layer"""

import json
with open('readworks_gradek.0.1.json', 'r') as op:
  lines = op.read()
jlines = json.loads(lines)
#----------------
#def gruQA
import os
import cPickle

import numpy as np

from keras.layers.embeddings import Embedding
from keras.layers import Dense, Merge, Dropout, RepeatVector
from keras.layers import recurrent
from keras.models import Sequential
from keras.layers.core import Flatten
from keras.preprocessing.sequence import pad_sequences

from nltk import word_tokenize

def load_glove(dim):
    """ Loads GloVe data.
    :param dim: word vector size (50, 100, 200)
    :return: GloVe word table
    """
    word2vec = {}

    path = "data/glove/glove.6B." + str(dim) + 'd'
    if os.path.exists(path + '.cache'):
        with open(path + '.cache', 'rb') as cache_file:
            word2vec = cPickle.load(cache_file)

    else:
        # Load n create cache
        with open(path + '.txt') as f:
            for line in f:
                l = line.split()
                word2vec[l[0]] = [float(x) for x in l[1:]]

        with open(path + '.cache', 'wb') as cache_file:
            cPickle.dump(word2vec, cache_file)

    print("Loaded Glove data")
    return word2vec



RNN = recurrent.GRU
EMBED_HIDDEN_SIZE = 50
SENT_HIDDEN_SIZE = 100
QUERY_HIDDEN_SIZE = 20
ANSWER_HIDDEN_SIZE = 10
BATCH_SIZE = 16
EPOCHS = 40

vocab = set()

def tokenize(txt):
  return word_tokenize(txt.lower())
st_len = []
q_len = []
a_len = []
size = 0
for exjson in jlines['exercises']:
  tk = tokenize(exjson['story']['text'])
  st_len.append(len(tk))
  vocab.update(tk)
  for qjson in exjson['questions']:
    size += 1
    tk = tokenize(qjson['text'])
    q_len.append(len(tk))
    vocab.update(tk)
    for ansjson in qjson['answerChoices']:
      tk = tokenize(ansjson['text'])
      a_len.append(len(tk))
      vocab.update(tk)

st_maxlen = max(st_len)
q_maxlen = max(q_len)
a_maxlen = max(a_len)
label2idx = {'A':0,'B':1}
idx2label = 'AB'

#lead 0 for padding <eos>
idx2word = ['<eos>']
idx2word.extend(list(vocab))
word2idx = dict(zip(idx2word, range(len(idx2word))))


sl = []
ql = []
aAl = []
aBl = []
ll = []
for exjson in jlines['exercises']:
  tk= tokenize(exjson['story']['text'])
  sv = [word2idx[tt] for tt in tk]
  for qjson in exjson['questions']:
    tk = tokenize(qjson['text'])
    qv = [word2idx[tt] for tt in tk]
    sl.append(sv)
    ql.append(qv)
    for ansjson in qjson['answerChoices']:
      tk = tokenize(ansjson['text'])
      av = [word2idx[tt] for tt in tk]
      if ansjson['label'] == 'A':
        aAl.append(av)
      if ansjson['label'] == 'B':
        aBl.append(av)
    lb_v = [0.,0.]
    lb_v[label2idx[qjson['correctAnswer']]] = 1.
    ll.append(lb_v)
assert(len(sl) == size)
assert(len(ql) == size)
assert(len(aAl) == size)
assert(len(aBl) == size)
assert(len(ll) == size)




Xs = pad_sequences(sl, maxlen=st_maxlen)
Xq = pad_sequences(ql, maxlen=q_maxlen)
XaA = pad_sequences(aAl, maxlen=a_maxlen)
XaB = pad_sequences(aBl, maxlen=a_maxlen)
Y = np.array(ll)



vocab_size = len(idx2word)

word_vector = load_glove(50)

embedding_weights = np.zeros((vocab_size,EMBED_HIDDEN_SIZE))
for word,index in word2idx.items():
  try:
    embedding_weights[index,:] = word_vector[word]
  except KeyError as E:
    embedding_weights[index, :] = np.random.uniform(-1, 1, (EMBED_HIDDEN_SIZE,))





sentrnn = Sequential()
sentrnn.add(Embedding(vocab_size, EMBED_HIDDEN_SIZE, input_length=st_maxlen, mask_zero=True, weights=[embedding_weights]))
sentrnn.add(Dropout(0.2))

qrnn = Sequential()
qrnn.add(Embedding(vocab_size, EMBED_HIDDEN_SIZE, input_length=q_maxlen, mask_zero=True, weights=[embedding_weights]))
qrnn.add(Dropout(0.2))
qrnn.add(RNN(EMBED_HIDDEN_SIZE, return_sequences=False))
qrnn.add(RepeatVector(st_maxlen))

aArnn = Sequential()
aArnn.add(Embedding(vocab_size, EMBED_HIDDEN_SIZE,
                   input_length=a_maxlen, mask_zero=True, weights=[embedding_weights]))
aArnn.add(Dropout(0.2))
aArnn.add(RNN(EMBED_HIDDEN_SIZE, return_sequences=False))
aArnn.add(RepeatVector(st_maxlen))

aBrnn = Sequential()
aBrnn.add(Embedding(vocab_size, EMBED_HIDDEN_SIZE,
                   input_length=a_maxlen, mask_zero=True, weights=[embedding_weights]))
aBrnn.add(Dropout(0.2))
aBrnn.add(RNN(EMBED_HIDDEN_SIZE, return_sequences=False))
aBrnn.add(RepeatVector(st_maxlen))

modelA = Sequential()
modelA.add(Merge([sentrnn, qrnn, aArnn], mode='sum'))
modelB = Sequential()
modelB.add(Merge([sentrnn, qrnn, aBrnn], mode='sum'))
model = Sequential()
model.add(Merge([modelA, modelB], mode='concat', concat_axis=1))
model.add(Flatten())
#model.add(RNN(EMBED_HIDDEN_SIZE, return_sequences=False))
model.add(Dense(EMBED_HIDDEN_SIZE, activation = 'relu'))
model.add(Dropout(0.2))
model.add(Dense(2, activation='sigmoid'))

model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=['accuracy'])


print('Training')
model.fit([Xs, Xq, XaA, XaB], Y, batch_size=BATCH_SIZE, nb_epoch=EPOCHS, validation_split=0.1)


loss, acc = model.evaluate([Xs, Xq, XaA, XaB], Y, batch_size=BATCH_SIZE)
print('Test loss / test accuracy = {:.4f} / {:.4f}'.format(loss, acc))
