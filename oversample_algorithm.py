import sys
import random
import numpy as np
from collections import Counter, defaultdict
import logging
from sklearn import svm
from scipy.spatial.distance import cdist
from scipy.spatial import distance_matrix
from sklearn.cluster import DBSCAN
from imblearn.under_sampling import EditedNearestNeighbours

logging.basicConfig(level=logging.INFO)


class ODG:

    def __init__(self, eps=0.08, min_pts=4, k=5, p=2, fit_borderline_ratio=True, borderline_ratio=0.6,
                 min_core_number=5,
                 noise_ratio=0.1, multiple_k=4, translations=True, noise_smote=True):
        """
        :param eps: Dbscan radius size.
        :param min_pts: Minimum number of points in the region.
        :param k: The value of k nearest neighbor.
        :param p: Distance metric.
        :param fit_borderline_ratio: To be or not to be adaptive to calculate the number of samples generated at the boundary point.
        :param borderline_ratio:  The ratio that generates data points at the boundary point.
        :param noise_ratio: When the number of noise points is less than a certain value, no data is generated.
        :param min_core_number: The minimum number of sample classes in each cluster.
        :param multiple_k: The maximum number of generated samples of a single minority class is several times that of K,
        which limits the number of generated samples to avoid generating regional malformations.
        :param noise_smote: In the method of generating data at the noise point,
        the default is True, that is, use SMOTE method to generate the new sample point.
        :param translations: Whether to shift most of the class sample points.
        """
        self.eps = eps
        self.min_pts = min_pts
        self.borderline_ratio = borderline_ratio
        self.noise_ratio = noise_ratio
        self.multiple_k = multiple_k
        self.k = k
        self.p = p
        self.min_core_number = min_core_number
        self.translations = translations
        self.fit_borderline_radio = fit_borderline_ratio
        self.noise_smote = noise_smote

    def fit_sample(self, X, Y, k=-1, minority_class=None):
        if k == -1:
            k = self.k
        classes = np.unique(Y)
        classes_size = [sum(Y == c) for c in classes]
        if minority_class is None:
            minority_class = classes[np.argmin(classes_size)]
        num_sample, num_feature = X.shape[0], X.shape[1]
        num_minority = Counter(Y)[minority_class]
        num_majority = num_sample - num_minority
        minority_X = X[Y == minority_class]
        majority_X = X[Y != minority_class]
        minority_Y = Y[Y == minority_class]
        majority_Y = Y[Y != minority_class]
        num_oversample = num_majority - num_minority
        X = np.concatenate([minority_X, majority_X])
        Y = np.concatenate([minority_Y, majority_Y])
        classifier = DBSCAN(eps=self.eps, min_samples=self.min_pts)
        minority_cluster_label = classifier.fit_predict(minority_X)
        num_cluster = max(minority_cluster_label) + 1
        core_sample_indices = classifier.core_sample_indices_
        noise_sample_indices = np.arange(num_minority)[minority_cluster_label == -1]
        outline_sample_indices = np.ones(minority_cluster_label.shape[0])
        outline_sample_indices[noise_sample_indices] = 0
        outline_sample_indices[core_sample_indices] = 0
        outline_sample_indices = outline_sample_indices != 0
        outline_sample_indices = np.arange(num_minority)[outline_sample_indices]
        if len(noise_sample_indices) / num_minority < self.noise_ratio:
            num_oversample_noise = 0
        else:
            num_oversample_noise = int(self.radio_noise(len(noise_sample_indices) / num_minority) * num_oversample)
            num_oversample_noise = min(num_oversample_noise, self.multiple_k * k * len(noise_sample_indices))
        num_oversample -= num_oversample_noise
        if self.fit_borderline_radio:
            self.borderline_ratio = self.fit_alpha(len(outline_sample_indices) / num_minority)
        num_oversample_outline = num_oversample * self.borderline_ratio
        total_k_nearest_majority = 0
        cov_cluster, cluster_size = {}, {}
        for i in range(num_cluster):
            indices = np.tile([False], len(minority_Y))
            indices[core_sample_indices] = True
            indices[minority_cluster_label != i] = False
            if np.sum(indices) >= self.min_core_number:
                cluster_X = minority_X[indices]
            else:
                cluster_X = minority_X[minority_cluster_label == i]
            cov_cluster[i] = np.cov(cluster_X.T) / cluster_X.shape[0]
            cluster_size[i] = len(cluster_X)
        dist_mat = distance_matrix(minority_X, X, p=self.p)
        num_k_nearest_majority = defaultdict(lambda: 1e-3)
        translations = np.zeros(X.shape)
        for i in outline_sample_indices:
            dist_arr = dist_mat[i]
            k_nearest_idxes = np.argsort(dist_arr)[:k + 1]
            minority_cnt, majority_cnt = Counter(Y[k_nearest_idxes])[minority_class], k + 1 - \
                                         Counter(Y[k_nearest_idxes])[
                                             minority_class]
            if majority_cnt >= k or Y[k_nearest_idxes[0]] != minority_class:
                total_k_nearest_majority += num_k_nearest_majority[i]
                continue
            if majority_cnt > 0:
                num_k_nearest_majority[i] += majority_cnt
                max_dist = dist_arr[k_nearest_idxes[-1]]
                majority_idxes = np.array([arg for arg in k_nearest_idxes if Y[arg] != minority_class])
                translations[majority_idxes] += (X[majority_idxes] - X[i]) * (
                        (max_dist - dist_arr[majority_idxes]) / (1e-6 + dist_arr[majority_idxes])).reshape(-1, 1)
            total_k_nearest_majority += num_k_nearest_majority[i]
        if self.translations:
            X += translations
        oversample_outline_data = []
        for i in outline_sample_indices:
            cov = cov_cluster[minority_cluster_label[i]]
            num = min(int(k * self.multiple_k),
                      np.random.choice([0, 1]) + int(
                          num_oversample_outline * num_k_nearest_majority[i] / (total_k_nearest_majority + 1e-6)))
            oversample_outline_data.append(np.random.multivariate_normal(minority_X[i], cov, num))

        if len(oversample_outline_data) > 0:
            oversample_outline_data = np.concatenate(oversample_outline_data).reshape(-1, num_feature)
            new_label = np.array([minority_class] * oversample_outline_data.shape[0])
            X = np.concatenate([X, oversample_outline_data])
            Y = np.concatenate([Y, new_label])

        num_oversample_core = max(num_oversample - len(oversample_outline_data), 0)
        oversample_core_data = []
        for i in range(num_cluster):
            num_oversample_cluster = int(
                num_oversample_core * sum(minority_cluster_label == i) / (sum(minority_cluster_label != -1) + 1e-6))
            cluster_X = minority_X[minority_cluster_label == i]
            oversample_core_data.append(
                np.random.multivariate_normal(np.mean(cluster_X, axis=0), cov_cluster[i] * cluster_size[i],
                                              num_oversample_cluster))
        if len(oversample_core_data) > 0:
            oversample_core_data = np.concatenate(oversample_core_data).reshape(-1, num_feature)
            new_label = np.array([minority_class] * oversample_core_data.shape[0])
            X = np.concatenate([X, oversample_core_data])
            Y = np.concatenate([Y, new_label])

        oversample_noise_data = []
        if self.noise_smote:
            for _ in range(num_oversample_noise):
                i = np.random.choice(noise_sample_indices)
                dist_arr = dist_mat[i]
                k_nearest_idxes = np.argsort(dist_arr)[1:k + 1]
                point = X[np.random.choice(k_nearest_idxes)]
                rate = random.random()
                oversample_noise_data.append([point * rate + X[i] * (1 - rate)])
            if len(oversample_noise_data) > 0:
                oversample_noise_data = np.concatenate(oversample_noise_data).reshape(-1, num_feature)

        elif len(noise_sample_indices) > 1:
            noise_data = minority_X[noise_sample_indices]
            oversample_noise_data = np.random.multivariate_normal(np.mean(noise_data, axis=0), np.cov(noise_data.T),
                                                                  num_oversample_noise)
        if len(oversample_noise_data) > 0:
            new_label = np.array([minority_class] * oversample_noise_data.shape[0])
            X = np.concatenate([X, oversample_noise_data])
            Y = np.concatenate([Y, new_label])
        logging.info('Number of core production points :{}, number of boundary production points :{}, number of noise '
                     'production points :{}'.format(len(oversample_core_data), len(oversample_outline_data),
                                                    len(oversample_noise_data)))
        indices = np.arange(X.shape[0])
        np.random.shuffle(indices)
        X = X[indices]
        Y = Y[indices]
        return X, Y

    def fit_alpha(self, val):
        """
        Adaptive calculation of the generated sample ratio at the boundary points.
        :param val: Proportion of boundary sample points.
        :return: Percentage of the number of points of generation of boundary sample points.
        """
        return val ** (1 / 2)

    def radio_noise(self, radio):
        """
        Adaptive calculation of the generated sample ratio at the noise points.
        :param radio: Proportion of noise sample points.
        :return: Percentage of the number of points of generation of noise sample points
        """
        a = 0.9 / (1 - self.noise_ratio ** 2)
        return a * (radio ** 2) + 1 - a


def helper(class_matrix):
    """
    :param class_matrix: Mapping from a class to the corresponding matrix.
    :return: The merged matrix.
    """
    unpacked_points = []
    unpacked_labels = []
    for cls in class_matrix:
        if len(class_matrix[cls]) > 0:
            unpacked_points.append(class_matrix[cls])
            unpacked_labels.append(np.array([cls] * len(class_matrix[cls])))

    unpacked_points = np.concatenate(unpacked_points)
    unpacked_labels = np.concatenate(unpacked_labels)
    return unpacked_points, unpacked_labels


class MC_ODG:
    def __init__(self, p=2, k=7, eps=0.8, min_pts=4, fit_outline_radio=True, outline_radio=0.6, min_core_number=5,
                 noise_radio=0.3, multiple_k=4, translations=True, noise_smote=True):
        """
        :param eps: Dbscan radius size.
        :param min_pts: Minimum number of points in the region.
        :param k: The value of k nearest neighbor.
        :param p: Distance metric.
        :param fit_outline_radio: To be or not to be adaptive to calculate the number of samples generated at the boundary point.
        :param outline_radio:  The ratio that generates data points at the boundary point.
        :param noise_radio: When the number of noise points is less than a certain value, no data is generated.
        :param min_core_number: The minimum number of sample classes in each cluster.
        :param multiple_k: The maximum number of generated samples of a single minority class is several times that of K,
        which limits the number of generated samples to avoid generating regional malformations.
        :param noise_smote: In the method of generating data at the noise point,
        the default is True, that is, use SMOTE method to generate the new sample point.
        :param translations: Whether to shift most of the class sample points.
        """
        self.p = p
        self.k = k
        self.eps = eps
        self.min_pts = min_pts
        self.outline_radio = outline_radio
        self.min_core_number = min_core_number
        self.noise_radio = noise_radio
        self.multiple_k = multiple_k
        self.translations = translations
        self.fit_outline_radio = fit_outline_radio
        self.noise_smote = noise_smote

    def fit_sample(self, X, Y):
        classes = np.unique(Y)
        sizes = np.array([sum(Y == c) for c in classes])
        sorted_idxes = np.argsort(sizes)[::-1]
        classes = classes[sorted_idxes]
        class_matrix = {c: X[Y == c] for c in classes}
        n_max = max(sizes)
        for i in range(1, len(classes)):
            tem_class = classes[i]
            used_class_matrix = {}
            unused_class_matrix = {}
            for j in range(i):
                all_indices = list(range(len(class_matrix[classes[j]])))
                used_indices = np.random.choice(all_indices, min(int(n_max / i), len(all_indices)), replace=False)
                used_class_matrix[classes[j]] = [
                    class_matrix[classes[j]][idx] for idx in used_indices
                ]
                unused_class_matrix[classes[j]] = [
                    class_matrix[classes[j]][idx] for idx in all_indices if idx not in used_indices
                ]

            used_class_matrix[tem_class] = class_matrix[tem_class]
            unused_class_matrix[tem_class] = []

            for j in range(i + 1, len(classes)):
                used_class_matrix[classes[j]] = []
                unused_class_matrix[classes[j]] = class_matrix[classes[j]]

            unpacked_points, unpacked_labels = helper(used_class_matrix)
            sam_method = ODG(p=self.p, k=self.k, eps=self.eps, min_pts=self.min_pts,
                             borderline_ratio=self.outline_radio, translations=self.translations,
                             fit_borderline_ratio=self.fit_outline_radio, noise_smote=self.noise_smote,
                             min_core_number=self.min_core_number, noise_ratio=self.noise_radio,
                             multiple_k=self.multiple_k)
            over_sampled_points, over_sampled_labels = sam_method.fit_sample(unpacked_points, unpacked_labels,
                                                                             minority_class=tem_class)
            class_matrix = {}
            for cls in classes:
                class_oversampled_points = over_sampled_points[over_sampled_labels == cls]
                class_unused_points = unused_class_matrix[cls]
                if len(class_unused_points) == 0 and len(class_oversampled_points) == 0:
                    class_matrix[cls] = np.array([])
                elif len(class_oversampled_points) == 0:
                    class_matrix[cls] = class_unused_points
                elif len(class_unused_points) == 0:
                    class_matrix[cls] = class_oversampled_points
                else:
                    class_matrix[cls] = np.concatenate([class_oversampled_points, class_unused_points])

        unpacked_points, unpacked_labels = helper(class_matrix)
        return unpacked_points, unpacked_labels
