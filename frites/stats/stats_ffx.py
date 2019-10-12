"""Apply maximum statistics correction."""
import logging

import numpy as np

from mne.stats import fdr_correction, bonferroni_correction

from .stats_cluster import find_temporal_clusters

logger = logging.getLogger("frites")


###############################################################################
#                      FFX / TIME POINTS INFERENCES
###############################################################################

def ffx_maxstat(mi, mi_p, alpha=0.05):
    """Maximum statistics correction for fixed effect inference.

    Parameters
    ----------
    mi : array_like
        Array of mutual information of shape (n_roi, n_times)
    mi_p : array_like
        Array of permuted mutual information of shape (n_perm, n_roi, n_times)
    alpha : float | 0.05
        Significiency level

    Returns
    -------
    pvalues : array_like
        Array of p-values of shape (n_roi, n_times)

    References
    ----------
    Holmes et al., 1996 :cite:`holmes1996nonparametric`
    Nichols and Holmes, 2002 :cite:`nichols2002nonparametric`
    """
    logger.info(f"    FFX maximum statistics (alpha={alpha})")
    # prepare variables
    n_perm = mi_p.shape[0]
    pvalues = np.full_like(mi, 1.)
    # value to use as the threshold
    p_max = np.percentile(mi_p.max(axis=(1, 2)), 100. * (1. - alpha),
                          interpolation='higher')
    # infer p-values
    pvalues[mi > p_max] = alpha

    return pvalues


def _ffx_fdr_bonf(mi, mi_p, func, alpha=0.05):
    # prepare variables
    n_perm, n_roi, n_times = mi_p.shape
    meth_name = 'FDR' if 'fdr' in func.__name__ else 'Bonferroni'
    logger.info(f"    FFX {meth_name} correction (alpha={alpha})")
    # get p-values and apply the correction to it
    th_pval = np.sum(mi_p > mi, axis=0) / n_perm
    _, pvalues = func(th_pval, alpha)

    return pvalues


def ffx_fdr(mi, mi_p, alpha=0.05):
    """FDR correction for fixed effect inferences.

    Parameters
    ----------
    mi : array_like
        Array of mutual information of shape (n_roi, n_times)
    mi_p : array_like
        Array of permuted mutual information of shape (n_perm, n_roi, n_times)
    alpha : float | 0.05
        Significiency level

    Returns
    -------
    pvalues : array_like
        Array of p-values of shape (n_roi, n_times)
    """
    return _ffx_fdr_bonf(mi, mi_p, fdr_correction, alpha=alpha)


def ffx_bonferroni(mi, mi_p, alpha=0.05):
    """Bonferroni correction for fixed effect inferences.

    Parameters
    ----------
    mi : array_like
        Array of mutual information of shape (n_roi, n_times)
    mi_p : array_like
        Array of permuted mutual information of shape (n_perm, n_roi, n_times)
    alpha : float | 0.05
        Significiency level

    Returns
    -------
    pvalues : array_like
        Array of p-values of shape (n_roi, n_times)
    """
    return _ffx_fdr_bonf(mi, mi_p, bonferroni_correction, alpha=alpha)


###############################################################################
#                      FFX / CLUSTER INFERENCES
###############################################################################


def ffx_cluster_maxstat(mi, mi_p, alpha=0.05):
    """Maximum statistics for fixed effect and cluster level inferences.

    Parameters
    ----------
    mi : array_like
        Array of mutual information of shape (n_roi, n_times)
    mi_p : array_like
        Array of permuted mutual information of shape (n_perm, n_roi, n_times)
    alpha : float | 0.05
        Significiency level

    Returns
    -------
    pvalues : array_like
        Array of p-values of shape (n_roi, n_times)
    """
    # find threshold
    th = np.percentile(mi_p.max(axis=(1, 2)), 100. * (1. - alpha),
                       interpolation='higher')
    # infer p-values from cluster sizes
    logger.info(f"    FFX maximum statistics at cluster level (alpha={alpha},"
                f" cluster threshold={th})")
    pvalues = find_temporal_clusters(mi, mi_p, th, tail=1)

    return pvalues

def _ffx_cluster_fdr_bonf(mi, mi_p, func, alpha=0.05):
    # prepare variables
    n_perm = mi_p.shape[0]
    meth_name = 'FDR' if 'fdr' in func.__name__ else 'Bonferroni'
    # get p-values and apply the correction to it
    th_pval = np.sum(mi_p > mi, axis=0) / n_perm
    is_over_th = ~func(th_pval, alpha)[0]
    if not np.any(is_over_th):
        logger.warning(f"No MI exceed the threshold at p={alpha}")
        return np.full_like(mi, 1.)
    # find the threshold to apply
    th = mi[is_over_th].max()
    # infer p-values from cluster sizes
    logger.info(f"    FFX {meth_name} correction at cluster level "
                f"(alpha={alpha}, cluster threshold={th})")
    pvalues = find_temporal_clusters(mi, mi_p, th, tail=1)

    return pvalues


def ffx_cluster_fdr(mi, mi_p, alpha=0.05):
    """FDR correction for fixed effect and cluster level inferences.

    Parameters
    ----------
    mi : array_like
        Array of mutual information of shape (n_roi, n_times)
    mi_p : array_like
        Array of permuted mutual information of shape (n_perm, n_roi, n_times)
    alpha : float | 0.05
        Significiency level

    Returns
    -------
    pvalues : array_like
        Array of p-values of shape (n_roi, n_times)
    """
    return _ffx_cluster_fdr_bonf(mi, mi_p, fdr_correction, alpha=alpha)


def ffx_cluster_bonferroni(mi, mi_p, alpha=0.05):
    """Bonferroni correction for fixed effect and cluster level inferences.

    Parameters
    ----------
    mi : array_like
        Array of mutual information of shape (n_roi, n_times)
    mi_p : array_like
        Array of permuted mutual information of shape (n_perm, n_roi, n_times)
    alpha : float | 0.05
        Significiency level

    Returns
    -------
    pvalues : array_like
        Array of p-values of shape (n_roi, n_times)
    """
    return _ffx_cluster_fdr_bonf(mi, mi_p, bonferroni_correction, alpha=alpha)


def ffx_cluster_tfce(mi, mi_p, alpha=0.05):
    pass
