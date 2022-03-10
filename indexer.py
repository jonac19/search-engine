import json
from math import log
from os.path import getsize, isfile
from bs4 import BeautifulSoup
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
# Uses the external libraries NLTK and BeautifulSoup


class Indexer:
    def __init__(self):
        self.inverted_index = {}
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = stopwords.words("english")
        self.corpus_size = 0


    def start_indexing(self):
        """
        Constructs an inverted index of the corpus if one doesn't already
        exist. 
        """
        if isfile("INVERTED_INDEX.json"):
            return

        with open("WEBPAGES_RAW/bookkeeping.json", encoding="utf-8") as file:
            data = json.load(file)

            for file_path, url in data.items():
                print("Loading URL:", url, ", file path:", file_path)
                self.index(file_path, url)
                self.corpus_size += 1

        self.calculate_tf_idf()

        # Store the inverted index as a JSON file
        with open("INVERTED_INDEX.json", "w") as file:
            json.dump(self.inverted_index, file)


    def index(self, docID, url):
        """
        Indexes the webpage and adds it to the inverted index. Each token is
        associated with a postings list, where postings contain a docID, frequency
        of occurance in important HTML tags, indices of occurance, and
        TF-IDF score.
        """
        with open("WEBPAGES_RAW/" + docID, encoding="utf-8") as file:
            # Extract text from webpage, doesn't seem to handle broken HTML 100%
            soup = BeautifulSoup(file, "lxml")
            text = soup.get_text()
            # Track the token count of the webpage to calculate tf-idf
            words = word_tokenize(text)
            index_counter = 1
            for token in words:
                token = self.lemmatizer.lemmatize(token.lower())
                if self.is_token(token):
                    if token in self.inverted_index:
                        posting = self.inverted_index[token][-1]
                        # Case 1: Token exists in index and posting already exists
                        # for particular webpage
                        if posting["docID"] == docID:
                            posting["indices"].append(index_counter)
                        # Case 2: Token exists in index but no posting for
                        # particular webpage
                        else:
                            self.inverted_index[token].append({"docID": docID,
                                                               "html_tag_freq": 0,
                                                               "indices": [index_counter]})
                    # Case 3: Token does not exist in index yet
                    else:
                        self.inverted_index[token] = [{"docID": docID,
                                                       "html_tag_freq": 0,
                                                       "indices": [index_counter]}]
                index_counter += 1
            
            self.calculate_html_tag_freq(soup)


    def is_token(self, word):
        return len(word) > 2 and word not in self.stop_words


    def calculate_html_tag_freq(self, soup):
        """
        Calculates the important HTML tag frequency for the tokens in the given
        document. Important HTMl tags consist of the webpage's title, meta
        description, and meta keywords.
        """
        html_tag_tokens = set()
        html_tag_token_count = 0
        
        # Increases count if token is in title
        if soup.title and soup.title.string:
            for token in soup.title.string.split():
                token = self.lemmatizer.lemmatize(token.lower())
                if self.is_token(token) and token in self.inverted_index:
                    self.inverted_index[token][-1]["html_tag_freq"] += 1
                    html_tag_tokens.add(token)
                    html_tag_token_count += 1

        # Increases count if token is in meta description or meta keywords
        for meta_tag in soup("meta"):
            if meta_tag.get("name", None) == "description" or \
                    meta_tag.get("name", None) == "keywords":
                for token in meta_tag.get("content", "").split()[:10]:
                    token = self.lemmatizer.lemmatize(token.strip(",").lower())
                    if self.is_token(token) and token in self.inverted_index:
                        self.inverted_index[token][-1]["html_tag_freq"] += 1
                        html_tag_tokens.add(token)
                        html_tag_token_count += 1
        
        for html_tag_token in html_tag_tokens:
            posting = self.inverted_index[html_tag_token][-1]
            # Calculate document important HTML tag frequency
            if html_tag_token_count > 0:
                posting["html_tag_freq"] /= html_tag_token_count

        
    def calculate_tf_idf(self):
        """
        Calculates TF-IDF for all tokens in the inverted index using
        logarithmic TF and inverse DF.
        """
        for token in self.inverted_index:
            postings = self.inverted_index[token]

            # Calculate IDF
            doc_freq = len(postings)
            inverse_doc_freq = log(self.corpus_size / doc_freq)

            for posting in postings:
                # Calculate document TF-IDF
                log_freq = 1 + log(len(posting["indices"]))
                tf_idf = log_freq * inverse_doc_freq

                posting["tf-idf"] = tf_idf
