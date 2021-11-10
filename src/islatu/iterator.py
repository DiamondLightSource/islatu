# Copyright (c) 2021 Richard Brearton
# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Richard Brearton and Andrew R. McCluskey

def _get_iterator(to_iter, progress):
    """
    Create an iterator.

    Args:
        to_iter (:py:attr:`array_like`): The list or array to iterate.
        progress (:py:attr:`bool`): Show progress bar.

    Returns:
        :py:attr:`range` or :py:class:`tqdm.std.tqdm`: Iterator object.
    """
    iterator = range(len(to_iter))
    if progress:
        try:
            from tqdm import tqdm
            iterator = tqdm(range(len(to_iter)))
        except ModuleNotFoundError:
            print(
                "For the progress bar, you need to have the tqdm package "
                "installed. No progress bar will be shown"
            )
    return iterator
