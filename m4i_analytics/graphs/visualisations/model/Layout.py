from abc import ABCMeta


class Layout(object):

    __metaclass__ = ABCMeta

    @staticmethod
    def get_coordinates(graph, **kwargs):
        raise TypeError('The get_coordinates method has not been implemented for this layout!')
    # END get_coordinates

    @staticmethod
    def get_name():
        raise TypeError('The name property has not been implemented for this layout!')
    # END get_coordinates

# END Layout
