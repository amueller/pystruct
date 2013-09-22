#!/usr/bin/python
"""
This module provides a callable for easy evaluation of stored models.
"""
import argparse
from os.path import commonprefix
from numbers import Number
import matplotlib.pyplot as plt
import numpy as np

from pystruct.utils import SaveLogger

def halton(index, base):
       result = 0
       f = 1. / base
       i = index
       while(i > 0):
           result = result + f * (i % base)
           i = np.floor(i / base)
           f = f / base
       return result


def get_color(offset=0):
    i = 0
    while True:
        c1 = halton(i + offset, 2)
        c2 = halton(i + offset, 3)
        c3 = halton(i + offset, 5)
        i += 1
        yield [c1, c2, c3]


def main():

    parser = argparse.ArgumentParser(description='Plot learning progress for one or several SSVMs.')
    parser.add_argument('pickles', metavar='N', type=str, nargs='+',
                        help='pickle files containing SSVMs')
    parser.add_argument('--time', dest='time', action='store_const',
                        const=True, default=False, help='Plot against '
                       'wall-clock time (default: plot against iterations.)')
    parser.add_argument('--dual', dest='dual', action='store_const',
                        const=True, default=False, help='Plot primal and dual '
                       'values (default: plot primal suboptimality.)')
    parser.add_argument('--loss', dest='loss', action='store_const',
                        const=True, default=False, help='Plot loss '
                       'values (default: False.)')
    parser.add_argument('--absolute-loss', dest='absolute_loss', action='store_const',
                        const=True, default=False, help='Plot full loss value '
                       ' (default: plot difference to best loss.)')

    args = parser.parse_args()

    ssvms = []
    for file_name in args.pickles:
        print("loading %s ..." % file_name)
        ssvms.append(SaveLogger(file_name=file_name).load())
    if args.loss and np.any([hasattr(ssvm.logger, 'loss_') for ssvm in ssvms]):
        n_plots = 2
    else:
        n_plots = 1
    fig, axes = plt.subplots(1, n_plots)

    # find best dual value among all objectives
    if not args.dual:
        best_dual = -np.inf
        for ssvm in ssvms:
            if hasattr(ssvm, 'dual_objective_curve_'):
                best_dual = max(best_dual, np.max(ssvm.dual_objective_curve_))

    if not args.absolute_loss and n_plots ==2:
        best_loss = np.inf
        for ssvm in ssvms:
            best_loss = min(best_loss, np.min(ssvm.logger.loss_))
    else:
        best_loss = 0

    if args.dual or not np.isfinite(best_dual):
        best_dual = None


    for i, (ssvm, file_name, color) in enumerate(zip(ssvms, args.pickles, get_color(2))):
    #for i, (ssvm, file_name, color) in enumerate(zip(ssvms, args.pickles, colors)):
        prefix = ""
        if len(ssvms) > 1:
            common_prefix_length = len(commonprefix(args.pickles))
            prefix = file_name[common_prefix_length:-7] + " "
        plot_learning(ssvm, axes=axes, prefix=prefix, time=args.time,
                      color=color, suboptimality=best_dual,
                      loss_bound=best_loss, loss=args.loss)
    plt.show()


def plot_learning(ssvm, time=True, axes=None, prefix="", color=None,
    show_caching=False, suboptimality=None, loss_bound=0, loss=False):
    """Plot optimization curves and cache hits.

    Create a plot summarizing the optimization / learning process of an SSVM.
    It plots the primal and cutting plane objective (if applicable) and also
    the target loss on the training set against training time.
    For one-slack SSVMs with constraint caching, cached constraints are also
    contrasted against inference runs.

    Parameters
    -----------
    ssvm : object
        Learner to evaluate. Should work with all learners.

    time : boolean, default=True
        Whether to use wall clock time instead of iterations as the x-axis.

    prefix : string, default=""
        Prefix for legend.

    color : matplotlib color.
        Color for the plots.

    show_caching : bool, default=False
        Whether to include iterations using cached inference in 1-slack ssvm.

    suboptimality : float or None, default=None
        If a float is given, only plot primal suboptimality with respect to
        this optimum.

    loss_bound : float, default=0
        Lower bound for the loss for plotting in log-domain

    Notes
    -----
    Warm-starting a model might mess up the alignment of the curves.
    So if you warm-started a model, please don't count on proper alignment
    of time, cache hits and objective.
    """
    print(ssvm)
    if hasattr(ssvm, 'base_ssvm'):
        ssvm = ssvm.base_ssvm
    logger = ssvm.logger
    primal_objective = np.array(logger.primal_objective_)
    if suboptimality is not None:
        primal_objective -= suboptimality
    if len(logger.loss_) and loss:
        n_plots = 2
    else:
        n_plots = 1
    if axes is None:
        fig, axes = plt.subplots(1, n_plots)
    if not isinstance(axes, np.ndarray):
        axes = [axes]

    if time:
        inds = np.array(logger.timestamps_) / 60.
        axes[0].set_xlabel('training time (min)')
    else:
        axes[0].set_xlabel('Passes through training data')
        inds = np.arange(len(logger.timestamps_)) * logger.log_every
        #inds = logger.iterations_
    axes[0].set_title("Objective")
    axes[0].set_yscale('log')
    if suboptimality is None and len(logger.dual_objective_):
        primal_prefix = "primal objective"
        axes[0].plot(inds, logger.dual_objective_, '--', label=prefix + "dual objective", color=color, linewidth=3)
    else:
        primal_prefix = ""
    axes[0].plot(inds, primal_objective, label=prefix + primal_prefix,
                 color=color, linewidth=3)
    axes[0].legend(loc='best')
    if n_plots == 2:
        if time:
            axes[1].set_xlabel('training time (min)')
        else:
            axes[1].set_xlabel('Passes through training data')
        if not isinstance(logger.loss_[0], Number):
            # backward compatibility fix me!
            loss = [np.sum(l) for l in logger.loss_]
        else:
            loss = logger.loss_
        axes[1].plot(inds, np.array(loss) - loss_bound, color=color, linewidth=3)
        axes[1].set_title("Training Error (- %f)" % loss_bound)
        axes[1].set_yscale('log')
    return axes


if __name__ == "__main__":
    main()
