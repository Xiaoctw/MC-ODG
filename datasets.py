import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import LabelEncoder

logging.basicConfig(level=logging.INFO)

datasets = ['adult', 'automobile', 'breast-cancer-wisconsin', 'ecoli',
            'glass', 'haberman', 'transfusion', 'transfusion', 'wine', 'yeast']


def load_data(dataset):
    """
    :param dataset Select the imported data set
    Import the preprocessed data set. Details of different data sets are given in the paper.
    The data is placed in the Data folder
    transfusion: eps=0.15, min_pts=3, multiple_k inf ,outline_radio=0.5
    0: 570, 1: 178
    link：http://archive.ics.uci.edu/ml/machine-learning-databases/blood-transfusion/transfusion.data
    glass:eps=0.15, min_pts=3
    1: 76, 0: 69, 5: 29, 2: 17, 3: 13, 4: 9
    link：http://archive.ics.uci.edu/ml/machine-learning-databases/glass/glass.data
    breast-cancer-wisconsin: eps=0.5,min_pts=3,outline_radio=0.7
    2: 458, 4: 241
    link：http://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/breast-cancer-wisconsin.data
    wine: eps=0.36 min_pts=2
    1: 71, 0: 58, 2: 48
    link：http://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data
    adult: eps=1.6, min_pts=3,outline_radio=0.7
    0: 1029, 1: 499
    link：http://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data
    haberman：eps=0.14,min_pts=3,outline_radio=0.6,noise_radio=0.5
    0:225,1:81
    链接：http://archive.ics.uci.edu/ml/machine-learning-databases/haberman/haberman.data
    automobile：eps:1.8,min_pts=3,outline_radio=0.4,noise_radio=0.2
    1: 48, 2: 46, 3: 29, 0: 20, 4: 13
    ecoli：eps=0.14,min_pts=3,noise_radio=0.7
    'cp': 143, 'im': 77, 'pp': 52, 'imU': 35, 'om': 20, 'omL': 5, 'imS': 2, 'imL': 2
    link：http://archive.ics.uci.edu/ml/machine-learning-databases/ecoli/ecoli.data
    yeast：
    eps=0.13,min_pts=3,outline_radio=0.2,noise_radio=0.7
    0: 463, 7: 429, 6: 244, 5: 163, 4: 51, 3: 44, 2: 35, 9: 30, 8: 20, 1: 5}
    link：http://archive.ics.uci.edu/ml/machine-learning-databases/yeast/yeast.data
    """
    if dataset not in datasets:
        logging.error('There is no current data set')
    assert dataset in datasets
    file_name = dataset + '.csv'
    data_file = Path(__file__).parent / 'data' / file_name
    df = pd.read_csv(data_file)
    matrix = df.values
    X, Y = matrix[:, :-1], matrix[:, -1]
    Y = LabelEncoder().fit_transform(Y)
    logging.info('Data reading completed')
    return X, Y



