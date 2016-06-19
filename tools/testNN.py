import numpy as np

from agent import neuralTD1Agent

nnTest = neuralTD1Agent(9,5)

testInput = np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9])

nnTest.weight_InHide = np.array([[0.1,	0.2,	0.3,	0.4,	0.5,	0.6,	0.7,	0.8,	0.9,	0.3],
[0.1,	0.2,	0.3,	0.4,	0.5,	0.6,	0.7,	0.8,	0.9,	0.3],
[0.1,	0.2,	0.3,	0.4,	0.5,	0.6,	0.7,	0.8,	0.9,	0.3],
[0.1,	0.2,	0.3,	0.4,	0.5,	0.6,	0.7,	0.8,	0.9,	0.3],
[0.1,	0.2,	0.3,	0.4,	0.5,	0.6,	0.7,	0.8,	0.9,	0.3]]
                                )

nnTest.weight_HideOut = np.array([0.01,0.02,0.03,0.04,0.05,0.06])

nnTest.alpha=0.2
nnTest.parlambda=0.9
nnTest.e_InHide=np.zeros((5,10))
nnTest.e_HideOut=np.zeros((1,6))
tolerancia = 0.01

#TEST EVALUACION DE RED

resultadoEval = nnTest.eval(testInput)
matlabResult = 0.5508
print "Error entre esperado y eval ",abs(resultadoEval - matlabResult )
assert(abs(resultadoEval - matlabResult) < tolerancia)


#TEST DE BACKPROPAGATION
nextState = np.array([0.6555,0.1712,0.7060,0.0318,0.2769,0.0462,0.0971,0.8235,0.6948])

nnTest.backpropagate(testInput, nextState, 0, False)

weigthInMatlab = [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.3],
                  [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.3],
                  [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.3],
                  [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.3],
                  [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.3]]

weightOutMatlab =[0.0100,0.0200,0.0300,0.0400, 0.0500,0.0600]
eout1Matlab = [0.2216,    0.2216,    0.2216,    0.2216,    0.2216,   0.2477]
einMatlab = [
    [0.0002, 0.0000, 0.0002, 0.0000, 0.0001, 0.0000, 0.0000, 0.0002, 0.0002, 0.0002],
    [0.0003, 0.0001, 0.0003, 0.0000, 0.0001, 0.0000, 0.0000, 0.0004, 0.0003, 0.0005],
    [0.0005, 0.0001, 0.0005, 0.0000, 0.0002, 0.0000, 0.0001, 0.0006, 0.0005, 0.0007],
    [0.0006, 0.0002, 0.0007, 0.0000, 0.0003, 0.0000, 0.0001, 0.0008, 0.0006, 0.0009],
    [0.0008, 0.0002, 0.0008, 0.0000, 0.0003, 0.0001, 0.0001, 0.0010, 0.0008, 0.0012]
]

#Resultados
print "Test nnTest.weight_InHide ",np.allclose(nnTest.weight_InHide, weigthInMatlab)
print "Test nnTest.weight_HideOut ",np.allclose(nnTest.weight_HideOut, weightOutMatlab)
print "Test nnTest.e_InHide ", np.allclose(nnTest.e_InHide.round(4), einMatlab,rtol=1e-05)
print "Test nnTest.e_HideOut ", np.allclose(nnTest.e_HideOut.round(4), eout1Matlab,rtol=1e-05)
print ""