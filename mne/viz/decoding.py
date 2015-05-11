"""Functions to plot decoding results
"""
from __future__ import print_function

# Authors: Denis Engemann <denis.engemann@gmail.com>
#          Clement Moutard <clement.moutard@gmail.com>
#          Jean-Remi King <jeanremi.king@gmail.com>
#
# License: Simplified BSD

import numpy as np
import warnings


def plot_gat_matrix(gat, title=None, vmin=None, vmax=None, tlim=None,
                    ax=None, cmap='RdBu_r', show=True, colorbar=True,
                    xlabel=True, ylabel=True):
    """Plotting function of GeneralizationAcrossTime object

    Predict each classifier. If multiple classifiers are passed, average
    prediction across all classifier to result in a single prediction per
    classifier.

    Parameters
    ----------
    gat : instance of mne.decoding.GeneralizationAcrossTime
        The gat object.
    title : str | None
        Figure title. Defaults to None.
    vmin : float | None
        Min color value for score. If None, sets to min(gat.scores_).
        Defaults to None.
    vmax : float | None
        Max color value for score. If None, sets to max(gat.scores_).
        Defaults to None.
    tlim : array-like, (4,) | None
        The temporal boundaries. If None, expands to
        [tmin_train, tmax_train, tmin_test, tmax_test]
        Defaults to None.
    ax : object | None
        Plot pointer. If None, generate new figure. Defaults to None.
    cmap : str | cmap object
        The color map to be used. Defaults to 'RdBu_r'.
    show : bool
        If True, the figure will be shown. Defaults to True.
    colorbar : bool
        If True, the colorbar of the figure is displayed. Defaults to True.
    xlabel : bool
        If True, the xlabel is displayed. Defaults to True.
    ylabel : bool
        If True, the ylabel is displayed. Defaults to True.

    Returns
    -------
    fig : instance of matplotlib.figure.Figure
        The figure.
    """
    if not hasattr(gat, 'scores_'):
        raise RuntimeError('Please score your data before trying to plot '
                           'scores')
    import matplotlib.pyplot as plt
    if ax is None:
        fig, ax = plt.subplots(1, 1)

    # Define color limits
    if vmin is None:
        vmin = np.min(gat.scores_)
    if vmax is None:
        vmax = np.max(gat.scores_)

    # Define time limits
    if tlim is None:
        tt_times = gat.train_times['times_']
        tn_times = gat.test_times_['times_']
        tlim = [tn_times[0][0], tn_times[-1][-1], tt_times[0], tt_times[-1]]

    # Plot scores
    im = ax.imshow(gat.scores_, interpolation='nearest', origin='lower',
                   extent=tlim, vmin=vmin, vmax=vmax, cmap=cmap)
    if xlabel is True:
        ax.set_xlabel('Testing Time (s)')
    if ylabel is True:
        ax.set_ylabel('Training Time (s)')
    if title is not None:
        ax.set_title(title)
    ax.axvline(0, color='k')
    ax.axhline(0, color='k')
    ax.set_xlim(tlim[:2])
    ax.set_ylim(tlim[2:])
    if colorbar is True:
        plt.colorbar(im, ax=ax)
    if show is True:
        plt.show()
    return fig if ax is None else ax.get_figure()


def plot_gat_slice(gat, train_time='diagonal', title=None, xmin=None,
                   xmax=None, ymin=None, ymax=None, ax=None, show=True,
                   color='b', xlabel=True, ylabel=True, legend=True,
                   chance=True):
    """Plotting function of GeneralizationAcrossTime object

    Plot the scores of the classifier trained at \'train_time\'.

    Parameters
    ----------
    gat : instance of mne.decoding.GeneralizationAcrossTime
        The gat object.
    train_time : str | float. Default to 'diagonal'
        Plots a slice of gat.scores. If 'diagonal', plots scores of classifiers
        trained and tested at the same time, else plots scores of the
        classifier trained at train_time.
    title : str | None
        Figure title. Defaults to None.
    xmin : float | None, optional, defaults to None.
        Min time value.
    xmax : float | None, optional, defaults to None.
        Max time value.
    ymin : float | None, optional, defaults to None.
        Min score value. If None, sets to min(scores).
    ymax : float | None, optional, defaults to None.
        Max score value. If None, sets to max(scores).
    ax : object | None
        Plot pointer. If None, generate new figure. Defaults to None.
    show : bool, optional, defaults to True.
        If True, the figure will be shown. Defaults to True.
    color : str
        Score line color. Defaults to 'steelblue'.
    xlabel : bool
        If True, the xlabel is displayed. Defaults to True.
    ylabel : bool
        If True, the ylabel is displayed. Defaults to True.
    legend : bool
        If True, a legend is displayed. Defaults to True.
    chance : bool | float. Defaults to None
        Plot chance level. If True, chance level is estimated from the type
        of scorer.

    Returns
    -------
    fig : instance of matplotlib.figure.Figure
        The figure.
    """
    if not hasattr(gat, 'scores_'):
        raise RuntimeError('Please score your data before trying to plot '
                           'scores')
    import matplotlib.pyplot as plt
    if ax is None:
        fig, ax = plt.subplots(1, 1)

    # Detect whether gat is a full matrix or just its diagonal
    if np.all(np.unique([len(t) for t in gat.test_times_['times_']]) == 1):
        scores = gat.scores_
    elif train_time == 'diagonal':
        # Get scores from identical training and testing times even if GAT
        # is not square.
        scores = np.zeros(len(gat.scores_))
        for i, train_time in enumerate(gat.train_times['times_']):
            for test_times in gat.test_times_['times_']:
                # find closest testing time from train_time
                j = np.abs(test_times - train_time).argmin()
                # check that not more than 1 classifier away
                if train_time - test_times[j] <= gat.train_times['step']:
                    scores[i] = gat.scores_[i][j]
    elif type(train_time) in [float, np.float64, np.float32]:
        idx = np.abs(gat.train_times['times_'] - train_time).argmin()
        if not idx:
            raise ValueError("No classifier trained at %s " % train_time)
        scores = gat.scores_[idx]
    else:
        raise ValueError("train_time must be \'diagonal\' or a float.")
    ax.plot(gat.train_times['times_'], scores, color=color,
            label="Classif. score")
    # Find chance level
    if chance is True:
        # XXX JRK This should probably be solved within sklearn?
        if gat.scorer_.__name__ is 'accuracy_score':
            chance = 1. / len(np.unique(gat.y_train_))
        elif gat.scorer_.__name__ is 'roc_auc_score':
            chance = 0.5
        else:
            chance = np.nan
            warnings.warn('Cannot find chance level from %s, specify chance'
                          ' level' % gat.scorer.__name__)
        ax.axhline(chance, color='k', linestyle='--', label="Chance level")
    if title is not None:
        ax.set_title(title)
    if ymin is None:
        ymin = np.min(scores)
    if ymax is None:
        ymax = np.max(scores)
    ax.set_ylim(ymin, ymax)
    if xmin is not None and xmax is not None:
        ax.set_xlim(xmin, xmax)
    if xlabel is True:
        ax.set_xlabel('Time (s)')
    if ylabel is True:
        ax.set_ylabel('Classif. score ({0})'.format(
                      'AUC' if 'roc' in repr(gat.scorer_) else r'%'))
    if legend is True:
        ax.legend(loc='best')
    if show is True:
        plt.show()
    return fig if ax is None else ax.get_figure()
