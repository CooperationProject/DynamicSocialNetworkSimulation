from Tkinter import *
import Tkinter as tk
import datetime
# from datetime import datetime
import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
import oauth2 as oauth
import urllib2 as urllib
import sched, time
from dateutil import tz
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import os
from gensim.corpora import Dictionary
from nltk.tokenize import RegexpTokenizer

tokenizer = RegexpTokenizer(r'\w+')
from nltk.tokenize import word_tokenize
from gensim.models import AuthorTopicModel
from pprint import pprint
import io
import tkFont as tkfont

global ATMModel
global nbdoc
nbdoc = 0

# get newly tweets from Twitter
api_key = "7xsUD0Fz9o2Xr1U7Nkk9gLmSc"
api_secret = "RlhmxtEeTF4JZQUlbsuH03CjX7idGWH4xXxS2fVOQsv32kLtX6"
access_token_key = "836173277403885569-MzfcL5QeZp9Nj1W1aL5SyJmMk10CIOf"
access_token_secret = "LQGDYGlhoMmJ7a8NCiDA3ctamcFeB6sruixrwCRalFdNZ"


# get id from username
def getID(username):
    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token_key, access_token_secret)
    api = tweepy.API(auth)
    try:
        user = api.get_user(screen_name=username)
        return user.id
    except:
        return -1


def checkFollow(username1, username2):
    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token_key, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    friendshipobject = api.show_friendship(source_screen_name=username1, target_screen_name=username2)

    if "following=True" in str(friendshipobject[0]):
        a_follow_b = True
    else:
        a_follow_b = False

    if "following=True" in str(friendshipobject[1]):
        b_follow_a = True
    else:
        b_follow_a = False

    # print(a_follow_b)
    # print(b_follow_a)
    return a_follow_b, b_follow_a


# get 100 tweets of a user with id
_debug = 0

oauth_token = oauth.Token(key=access_token_key, secret=access_token_secret)
oauth_consumer = oauth.Consumer(key=api_key, secret=api_secret)

signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()

http_method = "GET"

http_handler = urllib.HTTPHandler(debuglevel=_debug)
https_handler = urllib.HTTPSHandler(debuglevel=_debug)


def twitterreq(url, method, parameters):
    req = oauth.Request.from_consumer_and_token(oauth_consumer,
                                                token=oauth_token,
                                                http_method=http_method,
                                                http_url=url,
                                                parameters=parameters)

    req.sign_request(signature_method_hmac_sha1, oauth_consumer, oauth_token)

    headers = req.to_header()

    if http_method == "POST":
        encoded_post_data = req.to_postdata()
    else:
        encoded_post_data = None
        url = req.to_url()

    opener = urllib.OpenerDirector()
    opener.add_handler(http_handler)
    opener.add_handler(https_handler)

    response = opener.open(url, encoded_post_data)

    return response


def fetchsamples(ids, usernames, period, startTime, endTime):
    NumberOfNewlyTweets = []
    for index, id in enumerate(ids, 0):
        # print("ID:", id)
        url = 'https://api.twitter.com/1.1/statuses/user_timeline.json?id=' + str(id) + '&count=100'
        parameters = []
        response = twitterreq(url, "GET", parameters)

        starttime = datetime.datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
        endtime = datetime.datetime.strptime(endTime, '%Y-%m-%d %H:%M:%S')

        for line in response:
            tweetsobjects = json.loads(line)
            text = ""
            for tweetobject in tweetsobjects:
                create_at = tweetobject["created_at"]
                create_at = str(create_at)[4:]

                datetime_object = datetime.datetime.strptime(create_at, '%b %d  %H:%M:%S +0000 %Y')
                datetime_object = datetime_object.strftime("%Y-%m-%d %H:%M:%S")
                datetime_object = datetime.datetime.strptime(datetime_object, '%Y-%m-%d %H:%M:%S')
                if datetime_object < endtime and datetime_object > starttime:
                    t = tweetobject['text']
                    # remove url
                    t = re.sub(r"http\S+", "", t)
                    t = t.strip()
                    t = t.replace("\n", "")
                    text = text + t + " "

            # Preprocessing text
            text = text.lower()
            # Remove punctuation.
            import string
            for c in string.punctuation:
                text = text.replace(c, "")
            # print("After remove punctuation:", text)

            # Keep only words (no numbers).
            text = ' '.join([token for token in text.split(" ") if not token.isdigit()])
            # print("After remove number:", text)

            # Remove common words from a stopword list.
            text = ' '.join([token for token in text.split(" ") if token not in stopwords.words('english')])
            # print("After remove stopwords:", text)

            # Stemming words in text
            ps = PorterStemmer()
            text = ' '.join([ps.stem(word) for word in text.split(" ")])

            # print("After stemming:", text)

            # remove character \u from text
            def remove_u(word):
                word_u = (word.encode('unicode-escape')).decode("utf-8", "strict")
                if r'\u' in word_u:
                    # print(True)
                    return word_u.split('\\u')[0]
                return word

            text = ' '.join([remove_u(each_word) for each_word in text.split(" ")])

            text = text.encode('utf-8').strip()
            # print("Final text:", text)

            if text != "":
                global nbdoc
                nbdoc += 1
                cwd = os.getcwd()
                perioddictionary = cwd + "/Dataset/" + period
                if not os.path.exists(perioddictionary):
                    os.makedirs(perioddictionary)
                filename = perioddictionary + "/" + str(nbdoc) + ".txt"
                with open(filename, "w") as f:
                    f.write(text)
                    f.close()

                # Save username-docname into file author-doc
                author_doc_file_name = "a" + period[6:] + ".txt"
                author_doc_file_path = cwd + "/Dataset/idx/" + author_doc_file_name
                with open(author_doc_file_path, "a") as f:
                    f.write('{}, '.format(usernames[index]))
                    f.write('{}\n'.format(nbdoc))
                    f.close()


# -----------------------------------------------------------------------------------------------------------------------
# Run ATM model

nb_topics = 5
topic_labels = []
for i in range(0, nb_topics):
    topic_labels.append(str(i))


# show some information related to author
def show_author(model, id, name):
    temp = {}
    temp.update({"id": id})
    # print('\n%s' % name)
    temp.update({"name": name})
    # print('Docs:', model.author2doc[name])
    temp.update({"Docs": model.author2doc[name]})
    # print('Topics:')
    # pprint([(topic_labels[topic[0]], topic[1]) for topic in model[name]])
    temp.update({"Topics": [(topic_labels[topic[0]], topic[1]) for topic in model[name]]})
    return temp


# run model
def corpus_author2doc(period):
    cwd = os.getcwd()
    data_dir = cwd + "\Dataset" + "/" + period
    files = os.listdir(data_dir)
    # Get all document texts and their corresponding IDs, read the files into memory.
    docs = []
    doc_ids = []
    for file in files:
        doc_id = file.split(".")[0]
        doc_ids.append(doc_id)

        # Read document text.
        # Note: ignoring characters that cause encoding errors.
        with io.open(data_dir + '/' + file, errors='ignore', encoding='utf-8') as fid:
            txt = fid.read()

        # Replace any whitespace (newline, tabs, etc.) by a single space.
        txt = re.sub('\s', ' ', txt)

        docs.append(txt)

    # Get all author names and their corresponding document IDs.
    try:
        author2doc = dict()
    except:
        author2doc = {}

    authorindex_dir = cwd + "\Dataset\idx"
    authorindexfilename = period[6:]
    filename = authorindex_dir + '/a' + authorindexfilename + ".txt"

    for line in io.open(filename, errors='ignore', encoding='utf-8'):
        # Each line corresponds to one author.
        contents = re.split(',', line)
        author_name = contents[0]
        # Remove any whitespace to reduce redundant author names.
        author_name = re.sub('\s', '', author_name)
        # Get document IDs for author.
        ids = [c.strip() for c in contents[1:]]
        if not author2doc.get(author_name):
            # This is a new author.
            author2doc[author_name] = []
            # Add document IDs to author.
            author2doc[author_name].extend([id for id in ids])

    # Use an integer ID in author2doc, instead of the IDs provided in dataset.
    # Mapping from ID of document in dataset, to an integer ID.
    # doc_id_dict = dict(zip(doc_ids, range(len(doc_ids))))
    doc_id_dict = {}
    for index, doc_id in enumerate(doc_ids):
        doc_id_dict.update({doc_id: index})
    # Replace IDs in dataset by integer IDs.
    for a, a_doc_ids in author2doc.items():
        for i, doc_id in enumerate(a_doc_ids):
            author2doc[a][i] = doc_id_dict[doc_id]

    # Pre-processing text
    processed_docs = []
    for doc in docs:
        # tokenize document string
        tokens = tokenizer.tokenize(doc)
        tokens_list = [i for i in tokens]
        processed_docs.append(tokens_list)

    docs = processed_docs
    del processed_docs

    # Create a dictionary representation of the documents, and filter out frequent and rare words.
    dictionary = Dictionary(docs)

    # Remove rare and common tokens.
    # Filter out words that occur too frequently or too rarely.

    # min_wordcount = 20
    # max_freq = 0.5
    # dictionary.filter_extremes(no_below=min_wordcount, no_above=max_freq)

    _ = dictionary[0]  # This sort of "initializes" dictionary.id2token.

    # Bag-of-words representation of the documents.
    corpus = []
    corpus = [dictionary.doc2bow(doc) for doc in docs]
    # print('Number of authors: %d' % len(author2doc))
    # print('Number of tokens: %d' % len(dictionary))
    # print('Number of documents: %d' % len(corpus))

    return corpus, author2doc, dictionary


def ATM(period):
    print(period)
    if period == "period0":
        train_corpus, train_author2doc, train_dictionary = corpus_author2doc(period)
        global ATMModel
        ATMModel = AuthorTopicModel(corpus=train_corpus, num_topics=nb_topics, id2word=train_dictionary.id2token,
                                    author2doc=train_author2doc, chunksize=2000, passes=1, eval_every=0, iterations=1,
                                    random_state=1, minimum_probability=0)

        author_list = []
        for index, author in enumerate(train_author2doc):
            dict = show_author(ATMModel, index, author)
            author_list.append(dict)

        import json
        filename = "User_Topics_Distribution_" + period + ".json"
        with open(filename, 'w') as fout:
            json.dump(author_list, fout)
    else:
        global ATMModel
        cwd = os.getcwd()
        perioddictionary = cwd + "/Dataset/" + period
        if os.path.exists(perioddictionary):
            new_corpus, new_author2doc, new_dictionary = corpus_author2doc(period)
            ATMModel.update(new_corpus, new_author2doc)
            author_list = []
            for index, author in enumerate(ATMModel.author2doc):
                dict = show_author(ATMModel, index, author)
                author_list.append(dict)

            import json
            filename = "User_Topics_Distribution_" + period + ".json"
            with open(filename, 'w') as fout:
                json.dump(author_list, fout)

        else:
            print("No more text information to update!!!!")



# -----------------------------------------------------------------------------------------------------------------------
# GUI
class Circle(Frame):
    def __init__(self, userids, usernames, period, startTime, endTime, ):
        Frame.__init__(self, bg="white")
        self.master.title("circle")
        self.grid()
        self.radius = 20
        self.canvas = Canvas(self, width=500, height=500, bg="white")
        self.canvas.grid(row=0, column=0)
        self.startTime = startTime
        self.endTime = endTime
        self.userids = userids
        self.usernames = usernames
        self.period = period
        self.FollowRelations = []
        self.MTPRelations = []
        self.normalFont = tkfont.Font(family="Helvetica", size=10)
        self.boldFont = tkfont.Font(family="Helvetica", size=12, weight="bold")

        # construct network
        self.canvas.create_text(117, 385, text="R1: Follow Relation", font=self.normalFont, fill="green")
        self.canvas.create_text(344, 385, text = "R2(topic's list): Major Topic Relation", font=self.normalFont, fill="red")
        self.canvas.create_text(267, 428, text="DYNAMIC NETWORK", fill='blue', font=self.boldFont)
        self.circlescoordinates = {"katyperry": (84, 126), "IvankaTrump": (193, 37), "realDonaldTrump": (343, 37),
                                   "HillaryClinton": (193, 209), "BillGates": (440, 209), "narendramodi": (440, 126),
                                   "BillClinton": (193, 322), "BarackObama": (343, 322), "LeoDiCaprio": (440, 322),
                                   "GeorgeHWBush": (84, 322)}

        self.linescoordinates = [["katyperry", "IvankaTrump", 96, 109, 176, 46],
                                 ["katyperry", "realDonaldTrump", 104, 120, 324, 44],
                                 ["katyperry", "narendramodi", 104, 126, 420, 126],
                                 ["katyperry", "HillaryClinton", 100, 137, 176, 198],
                                 ["katyperry", "BillGates", 103, 126, 323, 206],
                                 ["katyperry", "GeorgeHWBush", 82, 144, 82, 301],
                                 ["katyperry", "BillClinton", 88, 145, 180, 305],
                                 ["katyperry", "BarackObama", 100, 137, 329, 309],
                                 ["katyperry", "LeoDiCaprio", 102, 136, 429, 306],
                                 ["IvankaTrump", 'realDonaldTrump', 213, 38, 323, 38],
                                 ["IvankaTrump", 'HillaryClinton', 191, 56, 194, 188],
                                 ["IvankaTrump", 'BillGates', 203, 53, 422, 200],
                                 ["IvankaTrump", 'narendramodi', 210, 47, 420, 121],
                                 ["IvankaTrump", 'GeorgeHWBush', 186, 55, 87, 300],
                                 ["IvankaTrump", 'BillClinton', 194, 56, 192, 301],
                                 ["IvankaTrump", 'BarackObama', 197, 56, 329, 306],
                                 ["IvankaTrump", 'LeoDiCaprio', 204, 53, 424, 309],
                                 ["realDonaldTrump", 'HillaryClinton', 332, 53, 204, 191],
                                 ["realDonaldTrump", 'narendramodi', 359, 50, 427, 110],
                                 ["realDonaldTrump", 'BillGates', 348, 56, 425, 194],
                                 ["realDonaldTrump", 'GeorgeHWBush', 322, 37, 79, 302],
                                 ["realDonaldTrump", 'BillClinton', 335, 54, 201, 305],
                                 ["realDonaldTrump", 'BarackObama', 340, 55, 339, 302],
                                 ["realDonaldTrump", 'LeoDiCaprio', 346, 56, 432, 303],
                                 ['HillaryClinton', 'narendramodi', 213, 203, 422, 133],
                                 ['HillaryClinton', 'BillGates', 214, 210, 421, 210],
                                 ['HillaryClinton', 'GeorgeHWBush', 177, 221, 98, 308],
                                 ['HillaryClinton', 'BillClinton', 192, 228, 192, 300],
                                 ['HillaryClinton', 'BarackObama', 207, 224, 324, 314],
                                 ['HillaryClinton', 'LeoDiCaprio', 213, 216, 423, 311],
                                 ['narendramodi', 'BillGates', 437, 144, 437, 188],
                                 ['narendramodi', 'GeorgeHWBush', 424, 136, 95, 304],
                                 ['narendramodi', 'BillClinton', 423, 136, 204, 305],
                                 ['narendramodi', 'BarackObama', 428, 142, 344, 300],
                                 ['narendramodi', 'LeoDiCaprio', 440, 145, 440, 303],
                                 ['narendramodi', 'LeoDiCaprio', 440, 145, 440, 303],
                                 ['BillGates', 'GeorgeHWBush', 422, 216, 99, 308],
                                 ['BillGates', 'BillClinton', 421, 217, 207, 308],
                                 ["BillGates", "BarackObama", 429, 224, 353, 304],
                                 ['BillGates', 'LeoDiCaprio', 439, 229, 439, 302],
                                 ['GeorgeHWBush', 'BillClinton', 105, 323, 173, 323],
                                 ['GeorgeHWBush', 'BarackObama', 322, 323, 322, 322],
                                 ['BillClinton', 'BarackObama', 213, 323, 322, 323],
                                 ['BarackObama', 'LeoDiCaprio', 363, 325, 420, 325]]
        self.labelscoordinates = [['BillGates', 'BarackObama', 391, 264], ['BillGates', 'HillaryClinton', 312, 220],
                                  ['IvankaTrump', 'BillGates', 308, 115], ['BillGates', 'LeoDiCaprio', 446, 266],
                                  ['BillGates', 'narendramodi', 444, 166], ['BillGates', 'BillClinton', 313, 259],
                                  ['IvankaTrump', 'BarackObama', 270, 183], ['LeoDiCaprio', 'BarackObama', 389, 335],
                                  ['narendramodi', 'BarackObama', 376, 217], ['BillClinton', 'BarackObama', 260, 332],
                                  ['HillaryClinton', 'katyperry', 130, 173],
                                  ['HillaryClinton', 'BillClinton', 196, 264], ['katyperry', 'IvankaTrump', 125, 74],
                                  ['IvankaTrump', 'realDonaldTrump', 268, 26], ['IvankaTrump', 'LeoDiCaprio', 312, 188],
                                  ['IvankaTrump', 'narendramodi', 302, 84],
                                  ['narendramodi', 'realDonaldTrump', 398, 81],
                                  ['BillClinton', 'GeorgeHWBush', 139, 332]]

        for key, value in self.circlescoordinates.iteritems():
            self.canvas.create_oval(value[0] - self.radius, value[1] - self.radius, value[0] + self.radius,
                                    value[1] + self.radius, tags=usernames[0])
            self.canvas.create_text(value[0], value[1] + 30, text=key, tags=key)


        self.master.bind('<Configure>', self.resize)
        self.canvas.bind('<Button-1>', self.getUserTopicDistribution)
        self.canvas.focus_set()

        self.refresh()

    def refresh(self):
        print(self.period, self.startTime," - ",self.endTime)
        try:
            self.canvas.delete("lbTime")
        except:
            pass
        self.canvas.create_text(267, 455, text = str(self.startTime) + " - " + str(self.endTime), tag="lbTime", font=self.normalFont)

        # Crawl text infor and Run/Update ATM model
        fetchsamples(self.userids, self.usernames, self.period, self.startTime, self.endTime)
        ATM(self.period)

        # Update FollowRelations
        if len(self.FollowRelations)!=0:
            OldFollowRelations = self.FollowRelations
            for followrelation in OldFollowRelations:
                for line in self.linescoordinates:
                    if followrelation == [line[0], line[1]]:
                        self.canvas.delete(line[0] + "-" + line[1])
                        break
                    else:
                        if followrelation == [line[1], line[0]]:
                            self.canvas.delete(line[1] + "-" + line[0])
                            break

            self.canvas.delete("Follow")  # remove labels
            self.FollowRelations = []
            print("Delete lines between nodes!")

        for i, a in enumerate(self.usernames):
            for b in self.usernames[i + 1:]:
                a_follow_b, b_follow_a = checkFollow(a, b)
                if a_follow_b:
                    self.FollowRelations.append([a, b])
                if b_follow_a:
                    self.FollowRelations.append([b, a])

        for followrelation in self.FollowRelations:
            for line in self.linescoordinates:
                if followrelation == [line[0], line[1]]:
                    self.canvas.create_line(line[2], line[3], line[4], line[5], arrow="last",
                                            tag=line[0] + "-" + line[1])
                    break
                else:
                    if followrelation == [line[1], line[0]]:
                        self.canvas.create_line(line[2], line[3], line[4], line[5], arrow="first",
                                                tag=line[1] + "-" + line[0])
                        break
        print("Finish update Follow lines!")
        # Analysis Major topic relation from result of Topic distribution and update
        if len(self.MTPRelations)!=0:
            self.canvas.delete("MTP")
            self.MTPRelations = []

        filename = "User_Topics_Distribution_" + self.period + ".json"
        considerperiod = int(self.period[6:])
        while os.path.exists(filename) == False:
            considerperiod = considerperiod - 1
            filename = "User_Topics_Distribution_period" + str(considerperiod) + ".json"

        with open(filename) as data_file:
            data = json.load(data_file)

        for i, username1 in enumerate(self.usernames):
            for username2 in self.usernames[i + 1:]:
                if username1 != username2:
                    MTP = []
                    user1_topicdis = filter(lambda dataelement: dataelement['name'] == username1, data)[0][
                        "Topics"]
                    user2_topicdis = filter(lambda dataelement: dataelement['name'] == username2, data)[0][
                        "Topics"]
                    for i, each_topic in enumerate(user1_topicdis):
                        if user1_topicdis[i][1] >= 0.2 and user2_topicdis[i][1] >= 0.2:
                            MTP.append(user1_topicdis[i][0])
                    if len(MTP) > 0:
                        self.MTPRelations.append([username1, username2, MTP])

        # print("MTPRelation:", MTPRelations)
        try:
            self.canvas.delete("MTP")
            self.canvas.delete("Follow")
        except:
            pass

        labelcoordforMTPRelation = []
        for mtprelation in self.MTPRelations:
            for labelcoord in self.labelscoordinates:
                if mtprelation[0] in labelcoord and mtprelation[1] in labelcoord:
                    mtps = mtprelation[2]
                    temp = ""
                    for mtp in mtps:
                        temp = temp + mtp.encode("utf-8") + " "
                    temp = temp.strip()
                    label = '[R1, R2(' + temp + ')]'
                    self.canvas.create_text(labelcoord[2], labelcoord[3], text=label, tags="MTP")
                    labelcoordforMTPRelation.append(labelcoord)
                    break

        for labelcoord in self.labelscoordinates:
            if labelcoord not in labelcoordforMTPRelation:
                self.canvas.create_text(labelcoord[2], labelcoord[3], text='[R1]', tags="Follow")

        print("Finish add label for Relation major topic")
        #Update infor next period
        self.startTime = self.endTime
        now = datetime.datetime.now()
        now_plus_8h = now + datetime.timedelta(minutes=480)
        #self.endTime = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.endTime = str(now_plus_8h.strftime('%Y-%m-%d %H:%M:%S'))

        from_zone = tz.gettz('CET')
        to_zone = tz.gettz('GMT')
        utc = datetime.datetime.strptime(self.endTime, '%Y-%m-%d %H:%M:%S')
        utc = utc.replace(tzinfo=from_zone)
        self.endTime = utc.astimezone(to_zone)
        self.endTime = str(self.endTime)[:19]

        global periodindex
        periodindex += 1
        self.period = "period" + str(periodindex)

        print("Update process finish, wait next 8 hours to update!!!!")
        print("------------------------------------------------------------------------------------------")
        self.update_idletasks()
        self.after(28800000, self.refresh)

    def resize(self, event):
        self.canvas.configure(width=event.width - 4, height=event.height - 4)

    def getUserTopicDistribution(self, event):
        # when click into circle, we need to get newly topic's distribution and show
        self.canvas.delete("TopicDistribution")
        color = "red"  # self.getRandomColor()
        print event.x, event.y
        x = event.x
        y = event.y
        from matplotlib.patches import Circle
        for key, value in self.circlescoordinates.iteritems():
            circ = Circle(value, radius=self.radius)
            if circ.contains_point([x, y]):
                filename = "User_Topics_Distribution_" + self.period + ".json"
                considerperiod = int(self.period[6:])
                while os.path.exists(filename) == False:
                    considerperiod = considerperiod -1
                    filename = "User_Topics_Distribution_period" + str(considerperiod) + ".json"

                with open(filename) as data_file:
                    data = json.load(data_file)

                TopicDis = (filter(lambda dataelement: dataelement['name'] == key, data)[0]["Topics"])
                temp = []
                for topic in TopicDis:
                    temp.append(round(float(topic[1]), 2))
                self.canvas.create_text(value[0], value[1], text=str(temp), fill=color, tags="TopicDistribution")
                break



global StartTime, EndTime, userids, usersname_list, periodindex
userids = []
usersname_list = ["BillGates", "BarackObama", "HillaryClinton", 'katyperry', 'IvankaTrump', 'realDonaldTrump',
                  "LeoDiCaprio", "narendramodi", "BillClinton", "GeorgeHWBush"]
for username in usersname_list:
    userid = getID(username)
    userids.append(userid)

periodindex = 0
period = "period" + str(periodindex)

StartTime = "2017-01-01 00:00:00"
# get current time(get current local time and convert to GMT zone time)
EndTime = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))  # "2018-09-11 11:13:51"
from_zone = tz.gettz('CET')
to_zone = tz.gettz('GMT')
utc = datetime.datetime.strptime(EndTime, '%Y-%m-%d %H:%M:%S')
utc = utc.replace(tzinfo=from_zone)
EndTime = utc.astimezone(to_zone)
EndTime = str(EndTime)[:19]

Circle(userids, usersname_list, period, StartTime, EndTime).mainloop()

