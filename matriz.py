import mysql.connector
from mysql.connector import errorcode
import numpy as np
import pandas
import csv

#conecta ao bd e retorna objeto de conexão
def connect():
    try:
        cnx = mysql.connector.connect(user='jardel', password='jardel',
                                host='localhost',
                                database='deejai')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        return cnx

def sigmoid(x):
    return 1/(1+np.exp(-x))

def centroid(musics):
  n = len(musics) # numero de musicas
  m = len(musics[0]) # numero de caracteristicas
  center = np.zeros(m) # vetor centro das caracteristicas
  
  for music in musics:
    for i in range(m):
      center[i] = music[i] + center[i]
      
  center = center/n
  
  return center

room = "2"
#querrys sql
roomUsersQuerry = ("SELECT rooms_users.user_id FROM rooms_users WHERE room_id = %s" % room)
userTracksQuerry = ("SELECT users_tracks.user_id, users_tracks.track_id FROM users_tracks, (%s) roomUsers WHERE roomUsers.user_id = users_tracks.user_id" % roomUsersQuerry)
tracksQuerry = ("SELECT DISTINCT features.* FROM features, (%s) usertracks WHERE usertracks.track_id = features.track_id" % userTracksQuerry)

#track = 
singleTrackQuerry = ("SELECT * FROM features WHERE track_id = %s" )

def main():
    #conecta ao bd
    connection = connect()
    #faz uma requisição das musicas dos usuarios em uma sala
    cursor = connection.cursor()
    cursor.execute(tracksQuerry)

    #guarda features das musicas em um dicionario e salva lista de ids das musicas
    tracks = dict()
    trackList = []
    for id, track_id, danceability, energy, key, loudness, mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo, time_signature, duration_ms, active, createdAt, updatedAt in cursor:
        trackList.append(track_id)
        t = [danceability, energy, instrumentalness, liveness, speechiness, valence, acousticness, mode, sigmoid(duration_ms), sigmoid(key), sigmoid(time_signature), sigmoid(tempo), sigmoid(loudness)]
        tracks[track_id] = np.array(t)
    cursor.close()
    #print(tracks)
    #print("\n\n\n\n\n")
    
    #requisita as musicas de cada usuario na sala
    cursor = connection.cursor()
    cursor.execute(userTracksQuerry)

    userTracks = dict()
    #guarda tracks de cada usuario em um dicionario 
    for user_id, track_id in cursor:
        if user_id in userTracks:
            userTracks[user_id] = np.append(userTracks[user_id], track_id)
        else:
            userTracks[user_id] = np.array(track_id)
    
    #print(userTracks)

    #calcula centroide e variancia do usuario, baseado em suas musicas, e cria uma lista com ids dos usuarios
    userList = []
    users = dict()
    for i in userTracks:
        userTracksFeatures = []
        for track in userTracks[i]:
            userTracksFeatures.append(tracks[track])

        users[i] = [centroid(userTracksFeatures), np.var(userTracksFeatures)]
        userList.append(i)

    #monta matriz com notas, cada linha representa um usuario e cada coluna representa uma musica, a nota eh definida para todas as musicas de todos os usuarios da sala
    #a nota eh dada com base na variancia das musicas de um usuario sobre a distancia entre o centroide do usuario e as features da musica

    i = 0
    matrix = [[0 for x in range(3)] for y in range(len(users)* len(tracks))] 
    for user in users:
        for track in tracks:
            matrix[i][0] = user
            matrix[i][1] = track
            matrix[i][2] = 5*users[user][1]/np.linalg.norm(users[user][0]-tracks[track])  #nota_maxima*var/dist
            i = i+1


    # print("matriz ", matrix)
    # print("userlist =", userList)
    # print("tracklist =", trackList)

    # a = pandas.DataFrame(data=matrix)
    # a.to_csv(r'/home/jardel/Desktop/pandas.csv')
    # print(a)

    with open('./csv.csv','w') as myfile:
        wr = csv.writer(myfile) #, quoting=csv.QUOTE_ALL)
        wr.writerows(matrix)


if __name__ == "__main__":
    main()