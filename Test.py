from sys import *
import json

class TT:
    def __init__(self):
        self.a = 1
        self.b = 'asdf'

def isValidMessage(message, tabooWords):
    for tabooWord in tabooWords:
        if(message.lower().find(tabooWord) >= 0):
            return False
    return True

a = {'a': [1, 2, 3], 'b': [4, 5, 6], 'c': [7, 8, 9]}


chat = 'i hate professor'

print(TT())

