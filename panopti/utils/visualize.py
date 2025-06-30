import numpy as np

def to_rgb(x, cmap='bwr', filter_outliers=False):
    '''
    Convert a 1D numpy array to RGB colors using a matplotlib colormap.

    Parameters:
    x : np.ndarray
        1D numpy array to be converted to RGB colors.
    cmap : str
        Name of the matplotlib colormap to use. Default is 'bwr'.
    filter_outliers : bool
        If True, filter out the top and bottom 5% of values in x before mapping to colors.
        Default is False.
        
    Returns: np.ndarray (N, 3) RGB colors
    '''
    try:
        import matplotlib.pyplot as plt
        from matplotlib import cm
    except ImportError:
        raise ImportError("matplotlib is required for panopti.to_rgb(). Please install it with 'pip install matplotlib'.")
    # quantile based filtering:
    if filter_outliers:
        low_ = np.quantile(x, 0.05)
        high_ = np.quantile(x, 0.95)
        x = np.clip(x, low_, high_)

    signal = (x - x.min()) / (x.max() - x.min())
    cm_ = plt.get_cmap(cmap)
    signal = cm_(signal)[:,:3]
    return signal
