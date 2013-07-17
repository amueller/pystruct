import numpy as np
from numpy.testing import assert_array_equal

from pystruct.models import GridCRF, DirectionalGridCRF
from pystruct.learners import NSlackSSVM, SubgradientSSVM
import pystruct.toy_datasets as toy
from pystruct.inference import get_installed


def test_multinomial_blocks_cutting_plane():
    #testing cutting plane ssvm on easy multinomial dataset
    X, Y = toy.generate_blocks_multinomial(n_samples=10, noise=0.3,
                                           seed=0)
    n_labels = len(np.unique(Y))
    for inference_method in get_installed(['lp', 'qpbo', 'ad3']):
        crf = GridCRF(n_states=n_labels, inference_method=inference_method)
        clf = NSlackSSVM(model=crf, max_iter=10, C=100,
                         check_constraints=False)
        clf.fit(X, Y)
        Y_pred = clf.predict(X)
        assert_array_equal(Y, Y_pred)


def test_multinomial_blocks_directional():
    # testing cutting plane ssvm with directional CRF on easy multinomial
    # dataset
    X, Y = toy.generate_blocks_multinomial(n_samples=10, noise=0.3,
                                           seed=0)
    n_labels = len(np.unique(Y))
    for inference_method in get_installed(['lp', 'ad3']):
        crf = DirectionalGridCRF(n_states=n_labels,
                                 inference_method=inference_method)
        clf = NSlackSSVM(model=crf, max_iter=10, C=100,
                         check_constraints=False)
        clf.fit(X, Y)
        Y_pred = clf.predict(X)
        assert_array_equal(Y, Y_pred)


def test_multinomial_blocks_subgradient():
    #testing cutting plane ssvm on easy multinomial dataset
    X, Y = toy.generate_blocks_multinomial(n_samples=10, noise=0.3,
                                           seed=1)
    n_labels = len(np.unique(Y))
    crf = GridCRF(n_states=n_labels)
    clf = SubgradientSSVM(model=crf, max_iter=50, C=10, momentum=.98,
                          learning_rate=0.001, verbose=10)
    clf.fit(X, Y)
    Y_pred = clf.predict(X)
    assert_array_equal(Y, Y_pred)


def test_multinomial_checker_cutting_plane():
    X, Y = toy.generate_checker_multinomial(n_samples=10, noise=.1)
    n_labels = len(np.unique(Y))
    crf = GridCRF(n_states=n_labels)
    clf = NSlackSSVM(model=crf, max_iter=20, C=100000, check_constraints=True)
    clf.fit(X, Y)
    Y_pred = clf.predict(X)
    assert_array_equal(Y, Y_pred)


def test_multinomial_checker_subgradient():
    X, Y = toy.generate_checker_multinomial(n_samples=10, noise=0.0)
    n_labels = len(np.unique(Y))
    crf = GridCRF(n_states=n_labels)
    clf = SubgradientSSVM(model=crf, max_iter=50, C=10,
                          momentum=.98, learning_rate=0.01)
    clf.fit(X, Y)
    Y_pred = clf.predict(X)
    assert_array_equal(Y, Y_pred)
