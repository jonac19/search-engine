import json
from math import log, sqrt, ceil
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


class Querier:
    def __init__(self):
        self.load_data()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = stopwords.words("english")


    def run_console(self):
        """
        Displays the search engine in the console.
        """
        query = input("Please enter a query or 'q/Q' to quit: ").lower()

        while (query != "q"):
            results = self.retrieve(query)

            print()
            for result in results[:20]:
                print(f"{result[1]}")

            query = input("\nPlease enter a query or 'q/Q' to quit: ").lower()


    def load_data(self):
        """
        Loads the inverted index and corpus URLs.
        """
        with open("INVERTED_INDEX.json", encoding="utf-8") as file:
            self.inverted_index = json.load(file)

        with open("WEBPAGES_RAW/bookkeeping.json", encoding="utf-8") as file:
            self.urls = json.load(file)


    def retrieve(self, query):
        """
        Retrieves query results according to the ltc.ltc schema.
        """
        # Index elimination - high-idf query terms only
        q_terms = []
        for q_term in query.split():
            q_term = self.lemmatizer.lemmatize(q_term.lower())
            if q_term not in self.stop_words and q_term in self.inverted_index:
                q_terms.append(q_term)
        
        scores = self.score_documents(q_terms)

        # Return results sorted by cosine similarity from highest to lowest
        results = []
        for docID, _ in sorted(scores.items(), key=lambda x: -x[1]):
            results.append((docID, self.urls[docID]))

        return results


    def score_documents(self, q_terms):
        """
        Score all documents that are relevant to the query.
        """
        scores = {}

        self.calculate_cosine_similarities(q_terms, scores)
        self.calculate_html_tag_importance(q_terms, scores)
        self.calculate_proximity(q_terms, scores)

        return scores


    def calculate_cosine_similarities(self, q_terms, scores):
        """
        Calculates the cosine similarity scores for all documents that are
        relevant to the query.
        """
        cosine_similarities = {}
        
        q_len = 0
        doc_lens = {}
        for q_term in set(q_terms):
            # Calculate TF-raw
            q_term_tf_raw = q_terms.count(q_term)

            # Calculate TF-weighted
            q_term_tf_weighted = 1 + log(q_term_tf_raw)

            # Calculate idf from a document tf-idf
            # tf-idf / tf = idf
            posting = self.inverted_index[q_term][0]
            doc_tf = 1 + log(len(posting["indices"]))
            idf = posting["tf-idf"] / doc_tf

            # Calculate TF-IDF
            q_term_tf_idf = q_term_tf_weighted * idf

            q_len += q_term_tf_idf ** 2

            for posting in self.inverted_index[q_term]:
                docID = posting["docID"]
                doc_tf_idf = posting["tf-idf"]
                if docID in cosine_similarities:
                    cosine_similarities[docID].append(q_term_tf_idf * doc_tf_idf)
                    doc_lens[docID] += doc_tf_idf ** 2
                else:
                    cosine_similarities[docID] = [q_term_tf_idf * doc_tf_idf]
                    doc_lens[docID] = doc_tf_idf ** 2
        q_len = sqrt(q_len)

        # Index elimination - compute scores only for docs containing threshold
        # number of query terms
        q_term_threshold = ceil(len(set(q_terms)) / 2)

        for docID in cosine_similarities:
            doc_vals = cosine_similarities[docID]
            if len(doc_vals) >= q_term_threshold:
                cosine_similarity = sum(doc_vals) / (q_len * sqrt(doc_lens[docID]))
                scores[docID] = cosine_similarity


    def calculate_html_tag_importance(self, q_terms, scores):
        """
        Calculate the HTML tag importance score for all documents relevant to the
        query.
        """
        html_tag_freqs = {}
        for q_term in set(q_terms):
            for posting in self.inverted_index[q_term]:
                docID = posting["docID"]
                if docID in scores:
                    if docID in html_tag_freqs:
                        html_tag_freqs[docID].append(posting["html_tag_freq"])
                    else:
                        html_tag_freqs[docID] = [posting["html_tag_freq"]]

        for docID in html_tag_freqs:
            doc_vals = html_tag_freqs[docID]
            scores[docID] += sum(doc_vals) / len(doc_vals)


    def calculate_proximity(self, q_terms, scores):
        """
        Calculates the proximity score for all documents relevant to the query.
        """
        q_term_indices = {}
        for q_term in set(q_terms):
            for posting in self.inverted_index[q_term]:
                docID = posting["docID"]
                if docID in scores:
                    if docID in q_term_indices:
                        q_term_indices[docID].append(posting["indices"])
                    else:
                        q_term_indices[docID] = [posting["indices"]]

        for docID in q_term_indices:
            indices = q_term_indices[docID]
            smallest_window = None
            smallest_possible_window = len(indices)
            for index in indices[0]:
                bag_of_indices = [index] + self.get_bag_of_indices(index, indices[1:])
                window = max(bag_of_indices) - min(bag_of_indices) + 1
                
                if smallest_window == None or window < smallest_window:
                    smallest_window = window

                if smallest_window == smallest_possible_window:
                    break

            scores[docID] += smallest_possible_window / smallest_window


    def get_bag_of_indices(self, index, q_term_indices):
        """
        Recursive function that builds a bag of indices containing the closest
        grouping possible
        """
        # Base case where no more indices can be added to the bag of indices
        if len(q_term_indices) == 0:
            return []

        # Find the closest index to the given index
        cur_q_term_indices = q_term_indices[0]
        nearest_index = min(cur_q_term_indices, key=lambda x: abs(index - x))
        proximity = abs(index - nearest_index)

        bag_of_indices = []
        higher_index = index + proximity
        lower_index = index - proximity
        if q_term_indices[1:] != [] and higher_index in cur_q_term_indices and lower_index in cur_q_term_indices:
            bag_of_indices += min((self.get_bag_of_indices(higher_index, q_term_indices[1:]),
                                   self.get_bag_of_indices(lower_index, q_term_indices[1:])),
                                        key=lambda x: (max(x) - min(x)))
        elif higher_index in cur_q_term_indices:
            bag_of_indices.append(higher_index)
            bag_of_indices += self.get_bag_of_indices(higher_index, q_term_indices[1:])
        else:
            bag_of_indices.append(lower_index)
            bag_of_indices += self.get_bag_of_indices(lower_index, q_term_indices[1:])

        return bag_of_indices
