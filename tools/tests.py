
#if i store a game in the db and then i get the result the object should be the same
import MySQLdb

from utils import getGamefromDb,saveGameToDb
from utils import testGame
if __name__ == '__main__':
    db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    # cursor = db.cursor()
    cursor = db.cursor (MySQLdb.cursors.DictCursor)
    newGameId = saveGameToDb(cursor,testGame,'testing game store and retrieve')
    db.commit()
    cursor.close()
    db.close()



    db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    cursor = db.cursor (MySQLdb.cursors.DictCursor)
    game2Test=getGamefromDb(newGameId,cursor)
    assert(game2Test == testGame)
    cursor.close()
    db.close()
