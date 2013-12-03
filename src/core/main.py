#!/usr/bin/python
# -*-coding:utf-8 -*
""" Main du programme, permet le choix entre enregistrer un élément ou réaliser l'analyse d'un enregistrement déjà effectué """
import scipy.io.wavfile
import os
from utils.constantes import *
from numpy import abs,int16
from utils.db import Db
from recording.recorder import recorder
from recording.synchronisation import synchro
from handling.passe_haut import passe_haut
from handling.fenetre_hann import hann_window
from hmm.creationVecteurHMM import creeVecteur
from handling.triangularFilterbank import triangularFilter
from handling.inverseDCT import inverseDCTII
from hmm.tableauEnergyPerFrame import construitTableauEnergy
from handling.fft import *
from hmm.markov import buildHMMs, recognize, recognizeList

def main(verbose=True,action=-1,verboseUltime=True):
    db = Db("../../db/",verbose=verbose)
    choice = -1
    while( not choice in range(1,6) ):
        try:
            if verboseUltime:
                choice = int(input("Que voulez-vous faire ?\n1-Enregistrer un element\n\
2-Realiser l'analyse d'un mot\n3-Tester\n4-Afficher résultats intermédiaires\n5-Gestion des fichiers de la base de donnees\n"))
            else:
                choice = 2
        except NameError:
            print "Ceci n'est pas un nombre !"

    if choice == 1:
        #Réaliser un enregistrement
        recorder(db)
    elif choice == 2:
        fileOk = False
        while not fileOk:
            #On choisit le dossier à afficher
            print "Voici la liste des mots a etudier : "
            dirList = db.printDirFiles("waves/")
            dirChoice = -1
            while( not dirChoice in range(len(dirList)) ):
                try:
                    dirChoice = int( input( "Choisissez un fichier a traiter et entrez son numero : " ) )
                except NameError:
                    print "Ceci n'est pas un nombre !"
            print "Dossier choisi : ", dirList[dirChoice]
            fileOk = True
            numeroTraitement = 0
            filesList = db.printFilesList(dirList[dirChoice])
            print filesList
            action = int( input( "À partir de quelle action souhaitez-vous agir ?\n0-Tout\n1-Filtre passe-haut\n2-Fenêtre de Hann\n3-Transformée de Fourier Rapide\n4-Fonction Mel\n5-Création de la liste Mel\n6-Transformée de Fourier inverse\n7-Creation de vecteurs\n " ) )
            for f in filesList:
                dirName = os.path.dirname(f)
                m = db.getWaveFile(f)
                if action == 1:
                    content = m[1]
                elif action == 2:
                    content = db.getFile("handling/passe_haut_" + dirName + "_" + str(numeroTraitement) + ".txt")                
                elif action == 3:
                    content = db.getFile("handling/hann_" + dirName + "_" + str(numeroTraitement) + ".txt")
                elif action == 4:
                    content = db.getFile("handling/fft_" + dirName + "_" + str(numeroTraitement) + ".txt")
                elif action == 5:
                    content = db.getFile("handling/mel_" + dirName + "_" + str(numeroTraitement) + ".txt")
                elif action == 6:
                    content = db.getFile("handling/mel_tab_" + dirName + "_" + str(numeroTraitement) + ".txt")
                elif action == 7:
                    content = db.getFile("handling/fft_inverse_" + dirName + "_" + str(numeroTraitement) + ".txt")
                else:
                    content = m[1]
                mot,log = handlingOneWord(content,db,dirName,numeroTraitement)
                if verbose:
                    print log
                fileOk = False
                numeroTraitement+=1
    elif choice == 3:
        print "Vous allez d'abord réaliser l'enregistrement du mot que vous cherchez à tester"
        fileName = recorder(db,"tmp",1,False)
        freq,amp = db.getWaveFile("tmp/" + fileName + ".wav")
        m,l = handlingOneWord(amp,db,fileName,0)
        print m
    elif choice == 4:
        print "Voici la liste des mots a etudier : "
        dirList = db.printDirFiles("storage/handling/")
        dirChoice = -1
        while( not dirChoice in range(len(dirList)) ):
            try:
                dirChoice = int( input( "Choisissez un fichier a traiter et entrez son numero : " ) )
            except NameError:
                print "Ceci n'est pas un nombre !"
        print "Fichier choisi : ", dirList[dirChoice]
        amp = db.getFile("handling/" + str(dirChoice))
        db.addWaveFromAmp("output/" + str(dirChoice) + ".wav",44100,amp,"output/",False)
    elif choice == 5:
        choice3 = -1
        while( not choice3 in range(1,5) ):
            try:
                choice3 = int(input("Que voulez-vous faire ?\n1-Supprimer un fichier\n2-Supprimer un wav\n3-Synchroniser les wav\n4-Synchroniser tous les fichiers\n"))
            except NameError:
                print "Ceci n'est pas un nombre !"
        if choice3 == 1:
            print "Fichiers : "
            filesList = db.printDirFiles()
            dirName = "storage/"
        elif choice3 == 2:
            print "Dossiers des waves : "
            filesList = db.printDirFiles("waves/")
            dirName = "waves/"
        elif choice3 == 3:
            print "Voici la liste des mots a etudier : "
            dirList = db.printDirFiles("waves/")
            dirChoice = -1
            while( not dirChoice in range(len(dirList)) ):
                try:
                    dirChoice = int( input( "Quel mot souhaitez vous traiter?: " ) )
                except NameError:
                    print "Ceci n'est pas un nombre !"
            print "Dossier choisi : ", dirList[dirChoice]
            filesList = db.printFilesList(dirList[dirChoice])
            for f in filesList:
                ampli = db.getWaveFile(f)
                ampli2 = synchro(ampli[1], COEFF_LISSAGE, T_MIN, COEFF_COUPE)
                db.addWaveFromAmp("mod/" + f,ampli[0],ampli2)
        elif choice3 == 4:
            db.sync()
            db.sync("", "waves/")
    else:
        pass



def handlingOneWord(content,db,dirChoice,numeroTraitement,action=0,hmmList=[]):
    """ Fait le traitement d'un mot pour en construire les vecteurs de Markov et tester ensuite la compatibilité avec les automates existants 
            Retourne un tuple (motLePlusCompatible,log) """
    log = ""
    if action <= 1:
        log += "Filtre passe-haut en cours...\n"
        content = passe_haut(content)
        log += "Filtre passe-haut termine...\n"
        db.addFile("handling/passe_haut_" + str(dirChoice) + "_" + str(numeroTraitement) + ".txt",content)
        log += "Sauvegarde effectuee...\n\n"
    if action <= 2:
        log += "Fenêtre de Hann en cours...\n"
        content = hann_window(content)
        log += "Fenêtre de Hann terminee...\n"
        db.addFile("handling/hann_" + str(dirChoice) + "_" + str(numeroTraitement) + ".txt",content)
        log += "Sauvegarde effectuee...\n\n"
    if action <= 3:
        log += "Transformee de Fourier rapide en cours...\n"
        content = fftListe(content,True)
        energyTable = construitTableauEnergy(content)
        for k in range(len(content)):
            for l in range(len(content[k])):
                content[k][l]=abs(content[k][l])
        log += "Transformee de Fourier rapide terminee...\n"
        db.addFile("handling/fft_" + str(dirChoice) + "_" + str(numeroTraitement) + ".txt",content)
        log += "Sauvegarde effectuee...\n\n"
    """
    if action <= 4:
        log += "Application de la fonction Mel en cours..."
        for k in range(len(content)):
            content[k] = fct_mel_pas(content[k],10)
        log += "Application de la fonction Mel terminee..."
        db.addFile("handling/mel_" + str(dirChoice) + "_" + str(numeroTraitement) + ".txt",content)
        log += "Sauvegarde effectuee...\n"
    if action <= 5:    
        log += "Construction de la liste Mel en cours..."
        for k in range(len(content)):
            content[k] = mel_tab(content[k],10)
        log += "Construction de la liste Mel terminee..."
        db.addFile("handling/mel_tab_" + str(dirChoice) + "_" + str(numeroTraitement) + ".txt",content)
        log += "Sauvegarde effectuee...\n"
    """
    if action <=5:
        log += "Application de la fonction Mel en cours...\n"
        for k in range(len(content)):
            content[k] = triangularFilter(content[k],RATE)
        log += "Application de la fonction Mel terminee...\n"
        db.addFile("handling/mel_" + str(dirChoice) + "_" + str(numeroTraitement) + ".txt",content)
        log += "Sauvegarde effectuee...\n\n"
    if action <= 6:    
        log += "Transformee de Fourier inverse en cours...\n"
        for k in range(len(content)):
            content[k] = inverseDCTII(content[k])
        log += "Transformee de Fourier inverse terminee...\n"
        db.addFile("handling/fft_inverse_" + str(dirChoice) + "_" + str(numeroTraitement) + ".txt",content)
        log += "Sauvegarde effectuee...\n"
    if action <= 7:    
        log += "Creation de vecteurs HMM en cours...\n"
        content = creeVecteur(content, energyTable)
        log += "Creation de vecteurs HMM terminee...\n"
        db.addFile("handling/vecteurs_" + str(dirChoice) + "_" + str(numeroTraitement) + ".txt",content)
        log += "Sauvegarde effectuee...\n\n"
    db.logDump(str(dirChoice) + "_" + str(numeroTraitement),log)
    db.logDump(str(dirChoice) + "_" + str(numeroTraitement))
    buildHMMs(["Deux","Trois", "Cinq"],["../../db/storage/training/Deux.txt","../../db/storage/training/Trois.txt","../../db/storage/training/Cinq.txt"], 500)
    print "Mot reconnu : ", recognize(content)
    return motLePlusCompatible,log


#def handlingOneWord(content,db,dirChoice,numeroTraitement,action=0,hmmList=[]):
def test():
    db = Db("../../db/",verbose=False)
    fileName = recorder(db,"tmp",1,False,1)
    freq,amp = db.getWaveFile("tmp/" + fileName + ".wav")
    mot,log = handlingOneWord(amp, db, "test", 0)
    print "Mot reconnu : ", mot

test()

def ampToHMMFromList(content):
    return ""

if __name__ == "__main__":
    main(True)
