"""
Author: Arun Chaganty
"""

import itertools as it
import math, random

from collections import Counter

import util
from util import Counters

BEGIN_TAG = '-BEGIN-'

###############################################
# Problem 3.1. Linear Chain CRFs
###############################################

class LinearChainCRF(object):
    r"""
    This is a 'struct' that contains the specification of the CRF, namely
    the tags, featureFunction and parameters.
    """

    def __init__(self, tags, featureFunction, parameters = None ):
        r"""
        @param tags list string - The domain of y_t. For NER, these
               will be tags like PERSON, ORGANIZATION, etc.
        @param featureFunction function - Function that takes the time step
               t, previous tag y_{t-1}, current tag y_t, and observation
               sequence x, and returns a Counter representing the feature vector
               \phi_{local}(t, y_{t-1}, y_t, x).
               - E.g. unaryFeatureFunction, binaryFeatureFunction
        @param parameters Counter - parameters for the model (map from feature name to feature weight).
        """
        self.TAGS = tags
        self.featureFunction = featureFunction
        if parameters is None:
            parameters = Counter()
        self.parameters = parameters

    def G(self, t, y_, y, xs):
        r"""
        Computes one of the potentials in the CRF.
        @param t int - index in the observation sequence, 0-based.
        @param y_ string - value of of tag at time t-1 (y_{t-1}),
        @param y string - value of of tag at time t (y_{t}),
        @param xs list string - The full observation seqeunce.
        @return double - G_t(y_{t-1}, y_t ; x, \theta)
        """
        return math.exp( Counters.dot( self.parameters, self.featureFunction(t, y_, y, xs) ) )

####################################################3
# Problem 3.1a
def computeViterbi(crf, xs):
    """
    Compute the maximum weight assignment using the Viterbi algorithm.
    @params crf LinearChainCRF - the CRF model.
    @param xs list string - the sequence of observed words.
    @return list string - the most likely sequence of hidden TAGS.

    Tips:
    + Normalize Viterbi[i] at the end of every iteration (including 0!) to prevent numerical overflow/underflow.

    Possibly useful:
    - BEGIN_TAG
    - crf.TAGS ['-MISC-', '-ORG-', '-LOC-', '-PER-', '-O-']
    - crf.G(0, BEGIN_TAG, ys[0],xs)
    - Counter
    """
    # BEGIN_YOUR_CODE (around 20 lines of code expected)
    # viterbi is a list of counters; the list is indexed by time
    viterbi = [{}]
    s = 0
    for i in range(len(crf.TAGS)):
        s += crf.G(0, BEGIN_TAG, crf.TAGS[i], xs)
        viterbi[0][i]={'prob':crf.G(0, BEGIN_TAG, crf.TAGS[i], xs), 'prev': None}
    for i in range(len(crf.TAGS)):
        viterbi[0][i]['prob'] /= s
    for i in range(1, len(xs)):
        viterbi.append({})
        s = 0
        for j in range(len(crf.TAGS)):
            m = max(viterbi[i - 1][p]['prob'] * crf.G(i, crf.TAGS[p], crf.TAGS[j], xs) for p in range(len(crf.TAGS)))
            for k in range(len(crf.TAGS)):
                if (viterbi[i - 1][k]['prob'] * crf.G(i, crf.TAGS[k], crf.TAGS[j], xs) == m):
                    viterbi[i][j] = {'prob':m, 'prev':k}
                    s += m
                    break
        for n in range(len(crf.TAGS)):
            viterbi[i][n]['prob'] /= s
    m = max(v['prob'] for v in viterbi[-1].values())
    p = None
    seq = []
    for i, d in viterbi[-1].items():
        if (d['prob'] == m):
            seq.append(crf.TAGS[i])
            p = i
    for i in range(len(viterbi) - 2, -1, -1):
        seq.insert(0, crf.TAGS[viterbi[i +1][p]['prev']])
        p = viterbi[i +1][p]['prev']
    return seq
    # END_YOUR_CODE

####################################################3
# Problem 3.1b
def computeForward(crf, xs):
    r"""
    Computes the normalized version of
        Forward_t(y_{t}) = \sum_{y_{t-1}} G_t(y_{t-1}, y_t; x, \theta) Forward{t-1}(y_{t-1}).

    @params crf LinearChainCRF - the CRF
    @param xs list string - the sequence of observed words
    @return (double, list Counter) - A tuple of the computed
    log-normalization constant (A), and the sequence Forward_t; each member
    of the list is a counter that represents Forward_t

    Example output: (5.881, [
                Counter({'-FEAT-': 0.622, '-SIZE-': 0.377}),
                Counter({'-SIZE-': 0.761, '-FEAT-': 0.238}),
                Counter({'-SIZE-': 0.741, '-FEAT-': 0.258})])

    Tips:
    * In this version, you will need to normalize the values so that at
    each t, \sum_y Forward_t(y_t) = 1.0.
    * You will also need to collect the normalization constants z_t
      = \sum_{y_{t}} Forward_{t}(y_{t}) 
      to return the log partition function A = \sum_t \log(z_t). We need
      to take the log because this value can be extremely small or
      large.
    * Note that Forward_1(y_1) = G_1(-BEGIN-, y_1 ; x, \theta) before normalization.

    Possibly useful:
    - BEGIN_TAG
    - crf.G
    - crf.TAGS
    - Counter
    """
    A = 0.
    forward = [ None for _ in xrange(len(xs)) ]

    # BEGIN_YOUR_CODE (around 12-15 lines of code expected)
    forward[0]={}
    for i in range(len(crf.TAGS)):
        forward[0][crf.TAGS[i]] = crf.G(0, BEGIN_TAG, crf.TAGS[i], xs)
    A += math.log(sum(forward[0].values()))
    s = sum(forward[0].values())
    
    for j in forward[0].keys():
        forward[0][j] /= s
    
    for i in range(1, len(xs)):
        forward[i] = {}
        for j in range(len(crf.TAGS)):
            forward[i][crf.TAGS[j]] = sum(forward[i - 1][p] * crf.G(i, p, crf.TAGS[j], xs) for p in crf.TAGS)
        A += math.log(sum(forward[i].values()))
        s = sum(forward[i].values())
        for j in forward[i].keys():
            forward[i][j] /= s
    # END_YOUR_CODE

    return A, forward

####################################################3
# More utility functions

def computeBackward(crf, xs):
    r"""
    Computes a normalized version of Backward.

    @params crf LinearChainCRF - the CRF
    @param xs list string - the sequence of observed words
    @return list Counter - The sequence Backward_t; each member is a counter that represents Backward_t

    Example output: [
            Counter({'-SIZE-': 0.564, '-FEAT-': 0.435}),
            Counter({'-SIZE-': 0.567, '-FEAT-': 0.432}),
            Counter({'-FEAT-': 0.5, '-SIZE-': 0.5})]

    Tips:
    * In this version, you will need to normalize the values so that at
    each t, \sum_{y_t} Backward_t(y_t) = 1.0.

    Possibly useful:
    - BEGIN_TAG
    - crf.G
    - crf.TAGS
    - Counter
    """

    backward = [ None for _ in xrange(len(xs)) ]

    backward[-1] = Counter( { tag : 1. for tag in crf.TAGS } )
    z = sum(backward[-1].values())
    for tag in backward[-1]:
        backward[-1][tag] /= z

    for t in xrange( len(xs)-1, 0, -1 ):
        backward[t-1] = Counter({ tag :
                    sum( crf.G( t, tag, tag_, xs )
                        * backward[t][tag_] for tag_ in crf.TAGS )
                    for tag in crf.TAGS })
        z = sum(backward[t-1].values())
        for tag in backward[t-1]:
            backward[t-1][tag] /= z


    return backward

####################################################3
# Problem 3.1c
def computeEdgeMarginals(crf, xs):
    r"""
    Computes the marginal probability of tags,
    p(y_{t-1}, y_{t} | x; \theta) \propto Forward_{t-1}(y_{t-1})
            * G_t(y_{t-1}, y_{t}; x, \theta) * Backward_{t}(y_{t}).

    @param xs list string - the sequence of observed words
    @return list Counter - returns a sequence with the probability of observing (y_{t-1}, y_{t}) at each time step

    Example output:
    T = [ Counter({('-BEGIN-', '-FEAT-'): 0.561, ('-BEGIN-', '-SIZE-'): 0.439}),
          Counter({('-FEAT-', '-SIZE-'): 0.463, ('-SIZE-', '-SIZE-'): 0.343,
                   ('-SIZE-', '-FEAT-'): 0.096, ('-FEAT-', '-FEAT-'): 0.096}),
          Counter({('-SIZE-', '-SIZE-'): 0.590, ('-SIZE-', '-FEAT-'): 0.217,
                   ('-FEAT-', '-SIZE-'): 0.151, ('-FEAT-', '-FEAT-'): 0.041})
        ]

    Tips:
    * At the end of calculating f(y_{t-1}, y_{t}) = Forward_{t-1}(y_{t-1})
            * G_t(y_{t-1}, y_{t}; x, \theta) * Backward_{t}(y_{t}), you will
      need to normalize because p(y_{t-1},y_{t} | x ; \theta) is
      a probability distribution.
    * Remember that y_0 will always be -BEGIN-; at this edge case,
        Forward_{0}(y_0) is simply 1. So, T[0] = p(-BEGIN-, y_1 | x ; \theta)
        = G_1(-BEGIN-, y_1; x, \theta) Backward_1(y_1).

    * Possibly useful:
    - computeForward
    - computeBackward
    """

    _, forward = computeForward(crf, xs)
    backward = computeBackward(crf, xs)

    T = [ None for _ in xrange( len(xs) ) ]

    # BEGIN_YOUR_CODE (around 10 lines of code expected)
    T[0] = {}
    for i in range(len(crf.TAGS)):
        T[0][(BEGIN_TAG, crf.TAGS[i])] = crf.G(0, BEGIN_TAG, crf.TAGS[i], xs) * backward[0][crf.TAGS[i]]
    s = sum(T[0].values())
    for i in T[0].keys():
        T[0][i] /= s
    
    for i in range(1, len(xs)):
        T[i] = {}
        for j in range(len(crf.TAGS)):
            for k in range(len(crf.TAGS)):
                T[i][(crf.TAGS[k], crf.TAGS[j])] = forward[i - 1][crf.TAGS[k]] * crf.G(i, crf.TAGS[k], crf.TAGS[j], xs) * backward[i][crf.TAGS[j]]
        s = sum(T[i].values())
        for j in T[i].keys():
            T[i][j] /= s
    # END_YOUR_CODE
    return T

###############################################
# Problem 3.2. NER
###############################################

def unaryFeatureFunction(t, y_, y, xs):
    """
    Extracts unary features;
        - indicator feature on (y, xs[t])
    @param t int - index in the observation sequence, 0-based.
    @param y_ string - value of of tag at time t-1 (y_{t-1}),
    @param y string - value of of tag at time t (y_{t}),
    @param xs list string - The full observation seqeunce.
    @return Counter - feature vector
    """
    phi = Counter({
        (y, xs[t]) : 1,
        })
    return phi

def binaryFeatureFunction(t, y_, y, xs):
    """
    Extracts binary features;
        - everything in unaryFeatureFunction
        - indicator feature on (y_, y)
  @param t int - index in the observation sequence, 0-based.
    @param y_ string - value of of tag at time t-1 (y_{t-1}),
    @param y string - value of of tag at time t (y_{t}),
    @param xs list string - The full observation seqeunce.
    @return Counter - feature vector
    """
    phi = Counter({
        (y, xs[t]) : 1,
        (y_, y) : 1,
        })

    return phi

#################################
# Problem 3.2a
def nerFeatureFunction(t, y_, y, xs):
    """
    Extracts features for named entity recognition;
        - everything from binaryFeatureFunction
        - indicator feature on y and the capitalization of xs[t]
        - indicator feature on y and previous word xs[t-1]; for t=0, use 'PREV:-BEGIN-'
        - indicator feature on y and next word xs[t+1]; for t=len(xs)-1, use 'NEXT:-END-'
        - indicator feature on y and capitalization of previous word xs[t-1]; assume 'PREV:-BEGIN-' is not capitalized.
        - indicator feature on y and capitalization of next word xs[t+1]; assume 'PREV:-BEGIN-' is not capitalized.
    Check the assignment writeup for more details and examples.

    @param t int - index in the observation sequence, 0-based.
    @param y_ string - value of of tag at time t-1 (y_{t-1}),
    @param y string - value of of tag at time t (y_{t}),
    @param xs list string - The full observation seqeunce.
    @return Counter - feature vector

    Possibly useful
    - Counter
    """
    cap = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    # BEGIN_YOUR_CODE (around 18 lines of code expected
    out = {}
    
    for k in binaryFeatureFunction(t, y_, y, xs).keys():
        out[k] = binaryFeatureFunction(t, y_, y, xs)[k]
    
    if xs[t][0] in cap:
        out[(y, "-CAPITALIZED-")] = 1.0
    else:
        out[(y, "-CAPITALIZED-")] = 0.0
    
    if t == 0:
        out[(y, "PREV:"+"-BEGIN-")] = 1.0
    else:
        out[(y, "PREV:"+xs[t - 1])] = 1.0
    
    if t == (len(xs) - 1):
        out[(y, "NEXT:"+"-END-")] = 1.0
    else:
        out[(y, "NEXT:"+xs[t + 1])] = 1.0
    
    if(t != 0 and t != (len(xs) - 1)):
        if(xs[t - 1][0] in cap):
            out[(y, "-POST-CAPITALIZED-")] = 1.0
        else:
            out[(y, "-POST-CAPITALIZED-")] = 0.0
        if(xs[t + 1][0] in cap):
            out[(y, "-PRE-CAPITALIZED-")] = 1.0
        else:
            out[(y, "-PRE-CAPITALIZED-")] = 0.0
    elif t == 0:
        out[(y, "-POST-CAPITALIZED-")] = 0.0
    elif t == (len(xs) - 1):
        out[(y, "-PRE-CAPITALIZED-")] = 0.0
    
    return Counter(out)
    # END_YOUR_CODE

###############################################
# Problem 3.3 Gibbs sampling
###############################################

#################################
# Utility Functions

def gibbsRun(crf, blocksFunction, choiceFunction, xs, samples = 500):
    r"""
    Produce samples from the distribution using Gibbs sampling.
    @params crf LinearChainCRF - the CRF model.
    @params blocksFunction function - Takes the input sequence xs and
                returns blocks of variables that should be updated
                together.
    @params choiceFunction function - Takes
                a) the crf model,
                b) the current block to be updated
                c) the input sequence xs and
                d) the current tag sequence ys
                and chooses a new value for variables in the block based
                on the conditional distribution
                p(y_{block} | y_{-block}, x ; \theta).
    @param xs list string - Observation sequence
    @param samples int - Number of samples to generate
    @return generator list string - Generates a list of tag sequences
    """

    # Burn in is the number iterations to run from the initial tag
    # you've chosen before you generate the samples. It basically
    # prevents you from being biased based on your starting tag.
    BURN_IN = 100

    # Intitial value
    ys = [random.choice(crf.TAGS) for _ in xrange(len(xs))]

    # Get blocks
    blocks = blocksFunction(xs)

    # While burning-in, don't actually return any of your samples.
    for _ in xrange(BURN_IN):
        # Pick a 'random' block
        block = random.choice(blocks)
        # Update its values
        choiceFunction( crf, block, xs, ys )

    # Return a sample every epoch here.
    for _ in xrange(samples):
        # Pick a 'random' block
        block = random.choice(blocks)
        # Update its values
        choiceFunction( crf, block, xs, ys )
        # Return a sample
        yield tuple(ys)

#################################
# Problem 3.3a

def chooseGibbsCRF(crf, t, xs, ys):
    r"""
    Choose a new assignment for y_t from the conditional distribution
    p( y_t | y_{-t} , xs ; \theta).

    @param t int - The index of the variable you want to update, y_t.
    @param xs list string - Observation seqeunce
    @param ys list string - Tag seqeunce

    Tips:
    * You should only use the potentials between y_t and its Markov
      blanket.
    * You don't return anything from this function, just update `ys`
      in place.

    Possibly useful:
    - crf.G 
    - util.multinomial: Given a PDF as a list OR counter, util.multinomial draws
      a sample from this distribution; for example,
      util.multinomial([0.4, 0.3, 0.2, 0.1]) will return 0 with 40%
      probability and 3 with 10% probability.
      Alternatively you could use,
      util.multinomial({'a':0.4, 'b':0.3, 'c':0.2, 'd':0.1}) will return 'a' with 40%
      probability and 'd' with 10% probability.
    """
    # BEGIN_YOUR_CODE (around 11 lines of code expected)
    P = {}
    for j in crf.TAGS:
        if(t == 0):
            P[j] = crf.G(t, BEGIN_TAG, j, xs)
        else:
            P[j] = crf.G(t, ys[t - 1], j, xs)
    s = sum(P.values())
    for i in crf.TAGS:
        P[i] /= s
    ys[t] = util.multinomial(P)
    # END_YOUR_CODE

#################################
# Problem 3.3b

def computeGibbsProbabilities(crf, blocksFunction, choiceFunction, xs, samples = 2000):
    """
    Empirically estimate the probabilities of various tag sequences. You
    should count the number of labelings over many samples from the
    Gibbs sampler.
    @param xs list string - Observation sequence
    @param samples int - Number of epochs to produce samples
    @return Counter - A counter of tag sequences with an empirical
                      estimate of their probabilities.
    Example output:
        Counter({
        ('-FEAT-', '-SIZE-', '-SIZE-'): 0.379,
        ('-SIZE-', '-SIZE-', '-SIZE-'): 0.189,
        ('-FEAT-', '-SIZE-', '-FEAT-'): 0.166,
        ('-SIZE-', '-SIZE-', '-FEAT-'): 0.135,
        ('-FEAT-', '-FEAT-', '-SIZE-'): 0.053,
        ('-SIZE-', '-FEAT-', '-SIZE-'): 0.052,
        ('-FEAT-', '-FEAT-', '-FEAT-'): 0.018,
        ('-SIZE-', '-FEAT-', '-FEAT-'): 0.008})

    Possibly useful:
    * Counter
    * gibbsRun
    """
    # BEGIN_YOUR_CODE (around 2-3 lines of code expected)
    probs = {}
    samples = gibbsRun(crf, blocksFunction, chooseGibbsCRF, xs, samples)
    for i in samples:
        if i not in probs.keys():
            probs[i] = 1.0
        else:
            probs[i] += 1.0
    s = sum(probs.values())
    for i in probs.keys():
        probs[i] /= s
    return Counter(probs)
    # END_YOUR_CODE

#################################
# Problem 3.3c

def computeGibbsBestSequence(crf, blocksFunction, choiceFunction, xs, samples = 2000):
    """
    Find the best sequence, y^*, the most likely sequence using samples
    from a Gibbs sampler. This gives the same output as crf.computeViterbi.
    @param xs list string - Observation sequence
    @param samples int - Number of epochs to produce samples
    @return list string - The most probable tag sequence estimated using Gibbs.
    Example output:
        ('-FEAT-', '-SIZE-', '-SIZE-')

    Possibly useful:
    * Counter.most_common
    * gibbsRun
    """
    # BEGIN_YOUR_CODE (around 1 line of code expected)
    p = computeGibbsProbabilities(crf, blocksFunction, choiceFunction, xs, samples = 2000)
    return Counter.most_common(p)[0][0]
    # END_YOUR_CODE

#################################

# Example to help you debug

simpleCRF = LinearChainCRF( ["-FEAT-", "-SIZE-"],
        binaryFeatureFunction,
        Counter({
            ("-FEAT-", "-SIZE-") : 0.8,
            ("-SIZE-", "-FEAT-") : 0.5,
            ("-SIZE-", "-SIZE-") : 1.,
            ("-FEAT-", "Beautiful") : 1.,
            ("-SIZE-", "Beautiful") : 0.5,
            ("-FEAT-", "2") : 0.5,
            ("-SIZE-", "2") : 1.0,
            ("-FEAT-", "bedroom") : 0.5,
            ("-SIZE-", "bedroom") : 1.0,}))

exampleInput = "Beautiful 2 bedroom".split()
exampleTags = "-FEAT- -SIZE- -SIZE-".split()

