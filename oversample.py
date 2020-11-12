import argparse
import logging
from datasets import *
from oversample_algorithm import *

output_path = Path(__file__).parent / 'resampled_data'


def oversample_data(dataset, output_path, p=2, k=7, eps=0.8, min_pts=4, fit_borderline_ratio=True, borderline_ratio=0.6,
                    min_core_number=5,
                    noise_ratio=0.3, multiple_k=4, translations=True, noise_smote=True):
    X, Y = load_data(dataset)
    sampled_X, sampled_Y = MC_ODG(p, k, eps, min_pts, fit_borderline_ratio, borderline_ratio,
                                  min_core_number,
                                  noise_ratio, multiple_k, translations, noise_smote).fit_sample(X,
                                                                                                 Y)
    logging.info('Data oversampling is completed')
    data = np.c_[sampled_X, sampled_Y]
    csv_path = output_path / ('{}.csv'.format(dataset))
    pd.DataFrame(data).to_csv(csv_path, index=False)
    logging.info('Data written to file completed')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('-dataset', type=str, choices=datasets)
    parser.add_argument('-p', type=int, default=2)
    parser.add_argument('-k', type=int, default=7)
    parser.add_argument('-eps', type=float, default=0.8)
    parser.add_argument('-min_pts', type=int, default=4)
    parser.add_argument('-fit_borderline_ratio', type=bool, default=True)
    parser.add_argument('-borderline_ratio', type=float, default=0.6)
    parser.add_argument('-min_core_number', type=int, default=5)
    parser.add_argument('-noise_ratio', type=float, default=0.3)
    parser.add_argument('-multiple_k', type=int, default=10)
    parser.add_argument('-translations', type=bool, default=True)
    parser.add_argument('-noise_smote', type=bool, default=True)
    parser.add_argument('-output_path', type=str, default=output_path)
    oversample_data(**vars(parser.parse_args()))
