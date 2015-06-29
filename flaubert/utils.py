import pandas
from nltk.stem import wordnet
from fastcache import clru_cache
from sklearn.base import BaseEstimator, TransformerMixin
from pymaptools.iter import isiterable


TREEBANK2WORDNET = {
    'J': wordnet.wordnet.ADJ,
    'V': wordnet.wordnet.VERB,
    'N': wordnet.wordnet.NOUN,
    'R': wordnet.wordnet.ADV
}


def read_tsv(file_input, iterator=False, chunksize=None):
    """
    @rtype: pandas.core.frame.DataFrame
    """
    return pandas.read_csv(
        file_input, iterator=iterator, chunksize=chunksize,
        header=0, quoting=2, delimiter="\t", escapechar="\\", quotechar='"',
        encoding="utf-8")


def pd_row_iter(datasets, chunksize=1000):
    """Produce an iterator over rows in Pandas
    dataframe while reading from files on disk

    @param datasets: a list of filenames or file handles
    @param chunksize: how many lines to read at once
    """
    # ensure that silly values of chunksize don't get passed
    if not chunksize:
        chunksize = 1
    if not isiterable(datasets):
        datasets = [datasets]
    for dataset in datasets:
        for chunk in read_tsv(dataset, iterator=True, chunksize=chunksize):
            for row in chunk.iterrows():
                yield row


def pd_dict_iter(datasets, chunksize=1000):
    for idx, row in pd_row_iter(datasets, chunksize=chunksize):
        yield dict(row)


def pd_field_iter(field, datasets, chunksize=1000):
    """Produce an iterator over values for a particular field in Pandas
    dataframe while reading from files on disk

    @param field: a string specifying field name of interest
    @param datasets: a list of filenames or file handles
    @param chunksize: how many lines to read at once
    """
    for row in pd_row_iter(datasets, chunksize=chunksize):
        yield row[field]


def lru_wrap(func, cache_size=None):
    if cache_size:
        return clru_cache(maxsize=cache_size)(func)
    else:
        return func


def treebank2wordnet(treebank_tag):
    if not treebank_tag:
        return None
    letter = treebank_tag[0]
    return TREEBANK2WORDNET.get(letter)


def sum_dicts(*args):
    """Return a sum total of several dictionaries
    Note: this is non-commutative (later entries override earlier)"""
    result = dict()
    for arg in args:
        result.update(arg)
    return result


class ItemSelector(BaseEstimator, TransformerMixin):
    """For data grouped by feature, select subset of data at a provided key.
    The data is expected to be stored in a 2D data structure, where the first
    index is over features and the second is over samples.  i.e.
    >> len(data[key]) == n_samples
    Please note that this is the opposite convention to sklearn feature
    matrixes (where the first index corresponds to sample).
    ItemSelector only requires that the collection implement getitem
    (data[key]).  Examples include: a dict of lists, 2D numpy array, Pandas
    DataFrame, numpy record array, etc.
    >> data = {'a': [1, 5, 2, 5, 2, 8],
               'b': [9, 4, 1, 4, 1, 3]}
    >> ds = ItemSelector(key='a')
    >> data['a'] == ds.transform(data)
    ItemSelector is not designed to handle data grouped by sample.  (e.g. a
    list of dicts).  If your data is structured this way, consider a
    transformer along the lines of `sklearn.feature_extraction.DictVectorizer`.
    Parameters
    ----------
    key : hashable, required
        The key corresponding to the desired value in a mappable.
    """
    def __init__(self, key):
        self.key = key

    def fit(self, x, y=None):
        return self

    def transform(self, data_dict):
        return data_dict[self.key]
