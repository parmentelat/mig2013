################################################################################
#                                                                              #
#                             SpeechServer                                     #
#                           MIG SE Team 2013                                   # 
#                                                                              #
################################################################################


=== DESCRIPTION ===

SpeechServer is our interface that let authorized external applications 
(e.g. html5recorder) use our isolated speech recognition core.

=== How to use it ===

The server is running on port 8001 by default.
Send him POST Form requests, he will answer you with some nice XML


=== API ===

Always send in your POSTed Form the fields :

    user : your username
    hashedPass : your hashed password 
    clientDB : the id of the DB you want to interact with
    action : the action you want to do

Here are the actions you can do currently, and the fields you'll have to add
specifically :

    == "recognize_spoken_word" ==
        ''' Recognize an isolated spoken word from an audioBlob you provide '''

    audioBlob : the audioBlob whose type is specified by audioType
    audioType : the format of the audioBlob (custom "ogg" and 16bit 44.1 kHz
                    "wav" are supported)

    You will receive an XML doc of the following type :
    <respWord>the word that we have found for you if recognized</respWord>

Actions to be supported:

    == "add_word" ==

    == "list_word_records" ==

    == "rm_word_record" ==

    == "listen_recording" ==

=== Requirements ===

 - SpeechApp core module, obviously ...
 - Gstreamer1.0, gstreamer1.0-tools, gstreamer1.0-plugins-base, gstreamer1.0-plugins-good

    


