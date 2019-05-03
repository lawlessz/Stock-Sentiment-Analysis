#!/usr/bin/env python
# coding: utf8
"""Train a convolutional neural network text classifier on the
IMDB dataset, using the TextCategorizer component. The dataset will be loaded
automatically via Thinc's built-in dataset loader. The model is added to
spacy.pipeline, and predictions are available via `doc.cats`. For more details,
see the documentation:
* Training: https://spacy.io/usage/training

Compatible with: spaCy v2.0.0+
"""
from __future__ import unicode_literals, print_function
import plac
import random
from pathlib import Path
import thinc.extra.datasets
import mysqlClient
import pandas as pd
import spacy
from spacy.util import decaying

# spacy.prefer_gpu()
# nlp = spacy.load('en_core_web_lg')
from spacy.util import minibatch, compounding



model="tweetsClassifier\spacyTrainingModel"
output_dir=None
n_iter=5
n_texts=500


@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", "option", "m", str),
    output_dir=("Optional output directory", "option", "o", Path),
    n_texts=("Number of texts to train from", "option", "t", int),
    n_iter=("Number of training iterations", "option", "n", int)
)
def main(model=None, output_dir=None, n_iter=20, n_texts=2000):
    if model is not None:
        nlp = spacy.load(model)  # load existing spaCy model
        print("Loaded model '%s'" % model)
    else:
        nlp = spacy.blank('en')  # create blank Language class
        print("Created blank 'en' model")

    # add the text classifier to the pipeline if it doesn't exist
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if 'textcat' not in nlp.pipe_names:
        textcat = nlp.create_pipe('textcat')
        nlp.add_pipe(textcat, last=True)
    # otherwise, get it, so we can add labels to it
    else:
        textcat = nlp.get_pipe('textcat')

    # add label to text classifier
    textcat.add_label('Neutral')
    textcat.add_label('Bullish')
    textcat.add_label('Bearish')

    # load the IMDB dataset
    print("Loading tweets data...")
    # (train_texts, train_cats), (dev_texts, dev_cats) = load_data(limit=n_texts)
    (train_texts, train_cats), (dev_texts, dev_cats) = load_data_2(limit=n_texts)
    print("Using {} examples ({} training, {} evaluation)"
          .format(n_texts*2, len(train_texts), len(dev_texts)))
    train_data = list(zip(train_texts,
                          [{'cats': cats} for cats in train_cats]))

    # get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'textcat']
    dropout = decaying(0.6, 0.2, 1e-4)
    with nlp.disable_pipes(*other_pipes):  # only train textcat
        optimizer = nlp.begin_training()
        print("Training the model...")
        print('{:^5}\t{:^5}\t{:^5}\t{:^5}'.format('LOSS', 'P', 'R', 'F'))
        for i in range(n_iter):
            losses = {}
            # batch up the examples using spaCy's minibatch
            batches = minibatch(train_data, size=compounding(2., 8., 1.001))
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(texts, annotations, sgd=optimizer, drop=next(dropout),losses=losses)
            with textcat.model.use_params(optimizer.averages):
                # evaluate on the dev data split off in load_data()
                try:
                    scores = evaluate(nlp.tokenizer, textcat, dev_texts, dev_cats)
                    print('{0:.3f}\t{1:.3f}\t{2:.3f}\t{3:.3f}'  # print a simple table
                          .format(losses['textcat'], scores['textcat_p'],
                                  scores['textcat_r'], scores['textcat_f']))
                except Exception as e:
                    print(e)
                    pass

    # test the trained model
    test_text = "#aapl buy for 250m the market!!!"
    doc = nlp(test_text)
    print(test_text, doc.cats)

    if output_dir is None:
        output_dir = Path('tweetsClassifier/spacyTrainingModel')
        if not output_dir.exists():
            output_dir.mkdir()
        with nlp.use_params(optimizer.averages):
            nlp.to_disk(output_dir)
        print("Saved model to", output_dir)

        # test the saved model
        print("Loading from", output_dir)
        test_text = "long #aapl for 250m the market!!!"
        test_text2 = "#aapl lead the market!"
        nlp2 = spacy.load(output_dir)
        doc2 = nlp2(test_text)
        print(test_text, doc2.cats)


def load_data(limit=250, split=0.7):
    mysql_con = mysqlClient.mysql_connection()
    get_tweets_query = f"""
            SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.AMZN where contents like 'long%' or contents like 'bull%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.AMD where contents like 'long%' or contents like 'bull%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.AAPL where contents like 'long%' or contents like 'bull%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.GOOG where contents like 'long%' or contents like 'bull%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.FB where contents like 'long%' or contents like 'bull%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.MSFT where contents like 'long%' or contents like 'bull%'

        union all

        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.AMZN where contents like 'short%' or contents like 'bear%'
        union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.AMD where contents like 'short%' or contents like 'bear%'
        union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.AAPL where contents like 'short%' or contents like 'bear%'
        union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.GOOG where contents like 'short%' or contents like 'bear%'
        union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.FB where contents like 'short%' or contents like 'bear%'
                union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.MSFT where contents like 'short%' or contents like 'bear%'

        union all

        SELECT contents COLLATE utf8mb4_unicode_ci, 'neutral'  FROM tweets.AMZN where CATEGORY like 'neutral%'
        """
    tweets = mysql_con.select_query(get_tweets_query)
    tweets_df = pd.DataFrame(list(tweets),columns=['contents', 'category'])
    training_df_bullish = tweets_df.query("category == 'bullish'").sample(limit)
    training_df_bearish = tweets_df.query("category == 'bearish'").sample(limit)
    training_df_neutral = tweets_df.query("category == 'neutral'").sample(limit)
    """Load data from the IMDB dataset."""
    # Partition off part of the train data for evaluation
    train_data = pd.concat([training_df_bullish, training_df_bearish, training_df_neutral]).values.tolist()
    # train_data = pd.concat([training_df_positive, training_df_negative]).values.tolist()
    # train_data = [(Doc(i[0]), i[1]) for i in train_data]
    texts, labels = zip(*train_data)
    cats = [{'Neutral':float(y=='neutral'), 'Bullish': float(y == 'bullish'), 'Bearish': float(y == 'bearish')} for y in labels]
    # cats = [{'Bullish':float(y=='Positive'), 'Bearish':float(y=='Negative')} for y in labels]
    split = int(len(train_data) * split)
    return (texts[:split], cats[:split]), (texts[split:], cats[split:])


def load_data_2(limit=250, split=0.7):
    mysql_con = mysqlClient.mysql_connection()
    get_tweets_query = f"""
            SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.AMZN where contents like 'up%' or contents like 'buy%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.AMD where contents like 'up%' or contents like 'buy%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.AAPL where contents like 'up%' or contents like 'buy%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.GOOG where contents like 'up%' or contents like 'buy%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.FB where contents like 'up%' or contents like 'buy%'
        union all
        SELECT contents COLLATE utf8mb4_unicode_ci, 'bullish'  FROM tweets.MSFT where contents like 'up%' or contents like 'buy%'

        union all

        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.AMZN where contents like 'down%' or contents like 'sell%' or contents like 'crash%'
        union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.AMD where contents like 'down%' or contents like 'sell%' or contents like 'crash%'
        union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.AAPL where contents like 'down%' or contents like 'sell%' or contents like 'crash%'
        union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.GOOG where contents like 'down%' or contents like 'sell%' or contents like 'crash%'
        union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.FB where contents like 'down%' or contents like 'sell%' or contents like 'crash%'
                union all
        SELECT contents  COLLATE utf8mb4_unicode_ci, 'bearish'  FROM tweets.MSFT where contents like 'short%' or contents like 'bear%' or contents like 'crash%'

        union all

        SELECT contents COLLATE utf8mb4_unicode_ci, 'neutral'  FROM tweets.AMZN where CATEGORY like 'neutral%'
        """
    tweets = mysql_con.select_query(get_tweets_query)
    tweets_df = pd.DataFrame(list(tweets), columns=['contents', 'category'])
    training_df_bullish = tweets_df.query("category == 'bullish'").sample(limit, replace=True)
    training_df_bearish = tweets_df.query("category == 'bearish'").sample(limit, replace=True)
    training_df_neutral = tweets_df.query("category == 'neutral'").sample(limit, replace=True)
    """Load data from the IMDB dataset."""
    # Partition off part of the train data for evaluation
    train_data = pd.concat([training_df_bullish, training_df_bearish, training_df_neutral]).values.tolist()
    # train_data = pd.concat([training_df_positive, training_df_negative]).values.tolist()
    # train_data = [(Doc(i[0]), i[1]) for i in train_data]
    texts, labels = zip(*train_data)
    cats = [{'Neutral': float(y == 'neutral'), 'Bullish': float(y == 'bullish'), 'Bearish': float(y == 'bearish')} for y
            in labels]
    # cats = [{'Bullish':float(y=='Positive'), 'Bearish':float(y=='Negative')} for y in labels]
    split = int(len(train_data) * split)
    return (texts[:split], cats[:split]), (texts[split:], cats[split:])
# def load_data(limit=0, split=0.8):
#     """Load data from the IMDB dataset."""
#     # Partition off part of the train data for evaluation
#     train_data, _ = thinc.extra.datasets.imdb()
#     random.shuffle(train_data)
#     train_data = train_data[-limit:]
#     texts, labels = zip(*train_data)
#     cats = [{'POSITIVE': bool(y)} for y in labels]
#     split = int(len(train_data) * split)
#     return (texts[:split], cats[:split]), (texts[split:], cats[split:])


def evaluate(tokenizer, textcat, texts, cats):
    docs = (tokenizer(text) for text in texts)
    tp = 0.0  # True positives
    fp = 1e-8  # False positives
    fn = 1e-8  # False negatives
    tn = 0.0  # True negatives
    for i, doc in enumerate(textcat.pipe(docs)):
        gold = cats[i]
        # print(doc, gold, doc.cats)
        for label, score in doc.cats.items():
            if label not in gold:
                continue
            if score >= 0.5 and gold[label] >= 0.5:
                tp += 1.0
            elif score >= 0.5 and gold[label] < 0.5:
                fp += 1.0
            elif score < 0.5 and gold[label] < 0.5:
                tn += 1
            elif score < 0.5 and gold[label] >= 0.5:
                fn += 1
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f_score = 2 * (precision * recall) / (precision + recall)
    return {"textcat_p": precision, "textcat_r": recall, "textcat_f": f_score}

# def evaluate(tokenizer, textcat, texts, cats):
#     docs = (tokenizer(text) for text in texts)
#     tp = 0   # True positives
#     fp = 0  # False positives
#     fn = 0  # False negatives
#     tn = 0   # True negatives
#     for i, doc in enumerate(textcat.pipe(docs)):
#         gold = cats[i]
#         for label, score in doc.cats.items():
#             print(label, score, gold[label])
#             if label not in gold:
#                 continue
#             if score >= 0.5 and gold[label] >= 0.5:
#                 tp += 1.
#             elif score >= 0.5 and gold[label] < 0.5:
#                 fp += 1.
#             elif score < 0.5 and gold[label] < 0.5:
#                 tn += 1
#             elif score < 0.5 and gold[label] >= 0.5:
#                 fn += 1
#     # print("tp:", tp, "fp:", fp)
#     precision = tp / (tp + fp+1e-99)
#     recall = tp / (tp + fn+1e-99)
#     f_score = 2 * (precision * recall) / (precision + recall)
#     return {'textcat_p': precision, 'textcat_r': recall, 'textcat_f': f_score}

#
if __name__ == '__main__':
    plac.call(main)
